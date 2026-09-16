# TriggerTrade — Position Rules Methodology

**File:** `POSITION_RULES.md`  
**Version:** 1.2.15
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

**F-009 FIXED-mode prerequisites and output boundary.** Before evaluating the formulas, require a valid same-bound AVAILABLE F-008 Entry E, finite positive tick t with bound factual provenance, valid LONG/SHORT direction and pinned stop mode/configuration. A missing/nonfinite/nonpositive Entry uses `DEPENDENCY_ENTRY_UNAVAILABLE` or its upstream reason; missing/nonfinite/nonpositive tick uses `MISSING_EXCHANGE_FACT`. Invalid mode uses `CONFIG_INVALID`.

For FIXED only, S is an exact finite percentage where `1` means one percent:

```text
S > 0
LONG additionally: S < 100
```

Missing/malformed/nonfinite/out-of-domain fixed configuration yields `usable=false`, `CONFIG_INVALID`, with no default. No universal SHORT upper bound is inferred from LONG. DYNAMIC does not consume fixed_pct; a supplied fixed value in that mode remains ignored / NOT_APPLICABLE.

Apply exactly the outward tick normalization:

```text
LONG:  SL = floor(raw_sl / t) * t
SHORT: SL = ceil(raw_sl / t) * t
```

Require finite `SL > 0`, integer `SL/t`, the corresponding exact rounding equality, and protective side `SL < E` LONG / `SL > E` SHORT. Arithmetic or invariant failure yields `usable=false`, `ROUNDING_ERROR`, with no actionable stop. Do not clamp, offset, retry, change S/Entry, reprice or switch to DYNAMIC as repair. Retain raw/rounded values only as non-actionable diagnostics on failure.

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

**F-009 DYNAMIC-mode pass-through.** LONG consumes F-006; SHORT consumes F-007. The chosen branch must have `usable=true`, `reason=AVAILABLE`, and the same instrument, immutable direction, frozen handoff/digest, decision cycle/result, certified F-008 Entry, pinned Position configuration and tick provenance (or validated equivalent tick identity). Its selected reference and rounded stop pass through unchanged.

Unavailable or mismatched branch evidence rejects F-009 while retaining the original branch result/reason: `usable=false`, `reason=SL_UNAVAILABLE` or the dependency-specific reason, with `dependency_reason` equal to the original reason. Identity/provenance mismatch retains its mismatch diagnostics and may use `IDENTITY_INVALID` under the local reason mapping. Existing overall `SL_UNAVAILABLE -> REJECT` aggregation remains.

There is no second rounding, clamp, offset, fallback, weaker-reference retry, ATR recomputation or change of branch feasibility. Fixed-percentage validation is not a DYNAMIC gate. Only the same frozen usable stop can feed later sizing and economics.

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

The certified construction chain is:

```text
F-005 immutable Set direction
→ F-008 planned Entry
→ F-006 / F-007 directional dynamic stop, when DYNAMIC is selected
→ F-009 stop-mode result / F-010 Dynamic Take Profit
→ F-011 final quantity, notional and committed capital
→ F-012 final planned R:R and minimum net edge
```

For complete F-011/F-012 construction, initial Position approval, the matching
Portfolio grant and pinned Position configuration must already exist. F-008
Entry, F-009 Stop and F-010 Dynamic TP must be AVAILABLE/usable and share the
instrument, direction, cycle, handoff, grant, configuration and metadata
bindings. The retained Fixed TP methodology is not a substitute for the F-010
dependency in this certified chain. Stop and TP are F-011 construction
prerequisites, not quantity-sizing operands. F-008's identical Entry/LIMIT price
is consumed unchanged; LIMIT POST_ONLY is retained, LONG maps to BUY and SHORT
to SELL. Position never reinterprets Set direction.

This dependency statement does not move grant-dependent sizing, fees or full
F-012 evaluation into the initial OPPORTUNITY stage. P1's existing pre-grant
geometry/gross-R:R stage remains in place; no stage depends on a grant that its
own initial decision must precede.

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
C: the user's own-capital bound supplied by the matching, non-reserving Portfolio grant
```

Requirements:

```text
C = requested_capital_per_tranche
C > 0
finite exact decimal
C / Qcapital is an integer
same settlement/accounting currency as Portfolio Rules
same initial approval, cycle, handoff, grant, configuration and metadata bindings
```

If invalid:

```text
UNAVAILABLE / INVALID_CAPITAL_GRANT
```

A missing, malformed, nonfinite, nonpositive or Qcapital-unaligned grant
cannot produce usable construction. Do not round or repair an unaligned C.
Grant issuance does not reserve capital or create a hold. The local F-011
outcome above is aggregated under §43; unrelated generic S-003 reason names are
not renamed.

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

C is the non-reserving grant bound. Final F-011 construction determines
persisted committed capital H (defined in §20); Portfolio later holds and
accounts that same H. Neither C nor leveraged target notional T is automatically
reserved. In particular:

```text
T = target_order_notional = C × L
Portfolio hold amount after approval/confirmation = H
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
A = actual_committed_capital_exact = actual_order_notional / L
H = actual_committed_capital_persisted = ceil_Qcapital(A)
actual_committed_capital = H
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

For F-011 only, A denotes exact own capital, not the ATR symbol used in
Entry/Stop/TP Parts. Use the following exact local symbols and invariants:

```text
C = requested_capital_per_tranche
L = configured leverage
E = certified F-008 planned Entry / LIMIT price
q = qty_step
p = Qcapital = 0.000000000001
T = C * L
R = T / E
Q = q * floor(R / q)
N = Q * E
A = N / L
H = p * ceil(A / p)

Q / q is an integer
Q = q * floor(R / q)
T = C * L
R = T / E
N = Q * E
A = N / L
H = p * ceil(A / p)
A <= C
H <= C
```

Retain both capital-bound checks even though correct quantity flooring and an
aligned C imply them. A violation is CAPITAL_BOUND_VIOLATION, not permission to
repair a rounded value. Equality passes the inclusive bounds. No failed gate
permits clamping, splitting, resizing, changed leverage, a revised price or a
revised grant.

Existing Order Spec and confirmation scalars bind the same construction:
`entry.quantity = approved_quantity = Q`, `leverage = approved_leverage = L`,
`economics.target_order_notional = T`,
`economics.actual_order_notional = approved_actual_order_notional = N`, and
`economics.actual_committed_capital = approved_actual_committed_capital = H`.
There is no new wire field. T, Q, N and H serialize as complete exact finite
decimals; N is not rounded to Qcapital. Division preserves exact rational R/A;
when recurring, retain local reduced integer numerator / positive denominator
pairs encoded as strings, not external scalar contracts.

Retain the existing cycle/result/decision/grant/construction/plan/tranche IDs,
configuration identity/version/content digest, bound grant payload digest and
contract version, source/profile/metadata revisions, original venue facts,
Entry/Stop/TP identities and values, numeric policy, exact/rational construction
values, ordered gates/reasons, spec digest and confirmation scalars. Replay
uses these frozen facts, never a current API refresh. Changed content under an
identity, missing required replay evidence or inconsistent persisted outputs
fails closed and creates no new grant, approval or resized spec.

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

For F-011, C, L, E, qty_step, minimum quantity, minimum notional and venue
maximum leverage must be positive finite exact decimal facts with the required
units and provenance. `min_qty` is an alias for canonical `min_order_qty`, not
another threshold; the required contract field remains `min_order_qty`.
Contradictory supplied aliases, units or provenance, nonpositive/invalid facts,
or inconsistent min/max values reject. Do not round minimum/maximum thresholds
to the quantity grid.

`max_order_qty_status = AVAILABLE` requires:

```text
max_order_qty > 0
applicable provenance
max_order_qty >= min_order_qty
```

For the declared Bybit linear LIMIT POST_ONLY profile, require the applicable:

```text
lotSizeFilter.maxOrderQty
```

`max_order_qty_status = UNAVAILABLE` always prevents usable construction, even
if a stale numeric maximum accompanies it.

`max_order_qty_status = NOT_APPLICABLE` requires a null maximum and affirmative
evidence from the pinned profile that no maximum applies. Missing evidence
cannot establish non-applicability.

Unknown statuses, contradictory facts and unsupported non-applicability reject.
Facts come through Capital and Limits; Position performs no API refresh.

A correctly floored Q = 0 is QTY_ZERO_AFTER_FLOOR. Otherwise preserve the
inclusive minimum/maximum/notional checks above; equality passes. Independently
determinable failures are retained and ordered under the F-011 table in §43.
Failed construction exposes no approved/actionable sizing.

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

Under F-011 this is an exact equality, not an approximate comparison:

```text
margin_required = A = actual_order_notional / L
actual_committed_capital = H = ceil_Qcapital(A)
0 <= H - A < Qcapital
```

L must be a positive finite exact decimal with a valid positive venue maximum
and applicable provenance. Beyond finite decimal representation, L > 0 and the
supplied maximum, no integer, step, precision or L >= 1 restriction is added.
Invalid configured leverage and violated venue maximum retain their separate
local F-011 outcomes in §43.

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
For complete F-012 evaluation, require usable certified F-008 Entry, F-009
Stop, F-010 Dynamic TP and successful F-011 sizing, with matching instrument,
direction, cycle, handoff, configuration, grant and metadata bindings. E, SL,
TP, Q and N are positive finite exact decimals; require N = Q * E. Consume
final prices and quantity unchanged, retaining LIMIT POST_ONLY entry and MARKET
exits. No rerounding, resizing or repair is permitted. These post-grant
prerequisites do not displace P1's initial gross-opportunity evaluation.

Before applying the absolute-distance descriptions below, validate directional
geometry:

```text
s = 1 for LONG, -1 for SHORT
E = final certified Entry
Q = final certified quantity
N = actual_order_notional = Q * E
dr = s * (E - SL)
dw = s * (TP - E)

if dr = 0: FAIL / ZERO_RISK_DISTANCE; do not divide for R:R
otherwise if dr < 0 or dw <= 0: FAIL / INVALID_GEOMETRY
valid geometry requires dr > 0 and dw > 0
```

Only after these checks do the absolute-distance formulas represent the
certified risk/reward distances; they must not hide wrong-side geometry. For
valid geometry:

```text
risk_distance_price = dr
reward_distance_price = dw
risk_distance_pct = 100 * dr / E
reward_distance_pct = 100 * dw / E
gross_rr = dw / dr
gross_profit_tp = dw * Q
gross_loss_sl = dr * Q
```

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

F-012 uses exact finite **signed fractional rates**, applicable to the
bound instrument/account fee schedule and execution mechanics at the frozen
construction time. Require matching fee_schedule_version, fee_effective_at and
fee_rate_source_ref plus the existing identity/profile/configuration bindings.
Supported zero fees and negative rebates preserve their signs. Missing values
are not zero; there is no sign clamp, guessed rate, research-rate substitution
or fee refresh.

For formula-local reporting, missing/unavailable fee facts or provenance use
UNAVAILABLE / MISSING_EXCHANGE_FACT identifying the fee field. Malformed or
nonfinite rates, unsupported units or failed applicability use UNAVAILABLE /
INVALID_EXCHANGE_FACT; conflicting supplied bindings use IDENTITY_INVALID
with §43 precedence. The generic MISSING_FEE_RATE rejection above does not
replace these local F-012 distinctions. A-003's approved factual policy basis
is sufficient for these planned inputs; realized attribution is not being
substituted for planned economics.

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

Baseline attached TP execution is `MARKET`, so Position Rules uses the governed **taker fee rate frozen in the bound construction/grant**.

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

The bound factual rate and schedule/effective/source provenance remain
unchanged throughout calculation and replay. Position must not refresh the
rate after freezing. TP exit notional remains TP × Q, not Entry notional,
committed capital or target notional.

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

The F-012 baseline additional TP-cost set is empty:

```text
other_exchange_costs_if_deterministic = 0
entry_fee = N * maker_fee_rate
tp_exit_notional = TP * Q
tp_exit_fee = TP * Q * taker_fee_rate
tp_total_cost = entry_fee + tp_exit_fee
net_profit_tp = dw * Q - tp_total_cost
net_edge_pct = 100 * net_profit_tp / N
funding_in_planned_net_edge = false
```

An asserted applicable additional cost requires a separately approved
deterministic definition and reviewed integration. Without that authority,
economics is UNAVAILABLE / COST_POLICY_UNAVAILABLE; the asserted applicable
cost must not silently become zero. Funding, research spread/slippage and
simulated cost assumptions are not inserted into this certified planned edge.
The formula above uses actual notional N = Q × E in the denominator, never C,
H or target notional T.

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

The additional SL-cost set is empty in the certified baseline:

```text
other_deterministic_sl_costs = 0
sl_exit_notional = SL * Q
sl_exit_fee = SL * Q * taker_fee_rate
sl_total_cost = entry_fee + sl_exit_fee
```

The SL fee/net-R:R extension is an optional owner-local diagnostic, not an
additional external field or hard gate. As with §33, an asserted applicable
extra cost without separately approved deterministic definition and integration
uses COST_POLICY_UNAVAILABLE rather than silently inserting or zeroing it.
Planned funding remains excluded.

---

# 37. Net SL loss

Signed optional net-loss diagnostic (gross_loss_sl remains the positive
gross loss magnitude after valid geometry):

```text
net_loss_sl =
gross_loss_sl
+
sl_total_cost
```

Planned SL economics exclude funding, just as planned Net Edge does. Signed actual funding receipts/payments are accounted only after they occur by Lifecycle; planned fee/rebate signs remain preserved.

Supported signed rebates can make net_loss_sl zero or negative. That is
not itself a mandatory construction failure; §38 governs the optional net-R:R
denominator without converting the signed value to an absolute loss.

---

# 38. Net R:R diagnostic

Only when net_loss_sl > 0:

```text
net_rr = net_profit_tp / net_loss_sl
```

Otherwise:

```text
net_rr = null
diagnostic_status = UNAVAILABLE
diagnostic_reason = NONPOSITIVE_NET_LOSS_SL
```

Do not divide at a nonpositive denominator or repair it with absolute value,
infinity or fabricated zero. Diagnostic absence or undefined net R:R does not
reject an otherwise valid construction.

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

For the enabled comparison above, “Else” means that an evaluable enabled
comparison failed; it does not mean the rule was disabled. Enablement must be
an actual Boolean. An enabled configured_minimum_rr must be present and an
exact finite decimal; no default or additional positive lower bound is inferred.
Disabled thresholds are unused. Apply the exact local branches:

```text
disabled -> NOT_APPLICABLE
enabled with blocked prerequisite -> UNAVAILABLE
enabled and dw >= configured_minimum_rr * dr -> PASS
enabled and dw < configured_minimum_rr * dr -> FAIL / RR_BELOW_MINIMUM
```

The comparison requires previously validated dr > 0 and dw > 0. R:R and its
threshold are dimensionless; comparison uses exact pre-report values, not a
rounded ratio. Unknown enablement is CONFIG_INVALID, never fabricated disabled.
The local minimum_rr_result and existing economics.gross_rr do not add a
minimum_rr field to construction contract v5.

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

A disabled gate is never represented as fabricated `PASS`. Mandatory fee/economic/provenance outputs remain required even when this
gate is disabled.

Enablement must be an actual Boolean. An enabled threshold must be
present and an exact finite decimal, without an invented positivity bound;
a disabled threshold is unused. Compare in percent units, exactly:

```text
100 * net_profit_tp >= configured_minimum_net_edge_pct * N
N = Q * E > 0
```

Zero or negative net edge is valid signed data; the configured comparison
determines PASS/FAIL, including a nonpositive configured threshold. Disabled
rules remain NOT_APPLICABLE and blocked enabled rules remain UNAVAILABLE.
For local rule results, disabled configured_value is null; calculated_value is
the valid reported ratio when available, otherwise null; reasons for PASS and
NOT_APPLICABLE are null. An unknown flag is not represented as disabled.

Successful construction requires numeric planned net edge, maker/taker facts
and their provenance even with Minimum Net Edge disabled. Missing/invalid fees
therefore block construction while that disabled gate remains NOT_APPLICABLE.
Disabling both rules never bypasses dependencies, geometry, integrity or
required economics. Preserve the existing minimum_net_edge wire rule result.

Apply TT_NUMERIC_V1: exact decimal products/sums and exact rational division,
without intermediate rounding, binary floats or epsilon comparisons. Reports
use Qratio = 10^-18 and `Qratio * floor(exact_ratio / Qratio)`, including floor
toward negative infinity for negative values. Preserve reduced signed integer
numerator / positive denominator string pairs for exact ratios alongside their
canonical reports. Reporting quantization cannot decide either gate.

Retain the frozen dependency/configuration/grant/fee provenance, exact
construction values, numerical policy and ordered outcomes with the existing
identity/digest lineage for replay. Available diagnostic values from a non-PASS
result are not approved/actionable economics; no re-evaluation may refresh fees
or repair frozen prices/quantity.

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

### F-011 local construction results

Table order determines the primary reason. Preserve all determinable secondary
failures in that order, using ordinal field-name order for ties. Absent
dependency objects use their dependency reason; inconsistent supplied bindings
use `IDENTITY_INVALID`. A prerequisite-blocked gate is `UNAVAILABLE`, never
`PASS`; only a proven inapplicable maximum subcheck is `NOT_APPLICABLE`. Every
non-PASS construction exposes no approved/actionable sizing.

| Condition, in precedence order | Result / reason |
|---|---|
| Invalid initial-approval binding; inconsistent supplied identity, digest, provenance, direction, currency/unit/profile or required version | `UNAVAILABLE / IDENTITY_INVALID` |
| Missing or invalid pinned configuration envelope | `UNAVAILABLE / CONFIG_INVALID` |
| Missing grant or missing/malformed/nonfinite/nonpositive/Qcapital-unaligned `C` | `UNAVAILABLE / INVALID_CAPITAL_GRANT` |
| Missing/unusable F-008 Entry, F-009 Stop or F-010 TP; invalid respective price | `UNAVAILABLE / DEPENDENCY_ENTRY_UNAVAILABLE`, then `DEPENDENCY_STOP_UNAVAILABLE`, then `DEPENDENCY_TP_UNAVAILABLE`; preserve upstream reasons |
| Missing/malformed/nonfinite/nonpositive configured `L` | `FAIL / INVALID_LEVERAGE` |
| Missing required venue fact, status or provenance, accounting for the maximum-status rules | `UNAVAILABLE / MISSING_EXCHANGE_FACT` |
| Malformed/nonfinite/nonpositive required venue value; alias conflict; inconsistent min/max; unknown status or unsupported `NOT_APPLICABLE` | `UNAVAILABLE / INVALID_EXCHANGE_FACT` |
| `max_order_qty_status = UNAVAILABLE` | `UNAVAILABLE / MAX_ORDER_QTY_UNAVAILABLE` |
| `L >` valid `venue_max_leverage` | `FAIL / LEVERAGE_ABOVE_MAXIMUM` |
| Arithmetic failure or inconsistent floor/grid/product/ceiling/serialized-output invariant, excluding the separately checked capital bounds | `UNAVAILABLE / NUMERIC_INVARIANT_VIOLATION` |
| `A > C` or `H > C` | `FAIL / CAPITAL_BOUND_VIOLATION`; retain separate exact/persisted check results |
| Correctly floored `Q = 0` | `FAIL / QTY_ZERO_AFTER_FLOOR` |
| Positive `Q < min_order_qty` | `FAIL / QTY_BELOW_MINIMUM` |
| `AVAILABLE` maximum and `Q > max_order_qty` | `FAIL / QTY_ABOVE_MAXIMUM` |
| `N < min_notional` | `FAIL / NOTIONAL_BELOW_MINIMUM` |
| All required prerequisites, invariants and gates pass | `PASS / AVAILABLE` |

### F-012 local planned-economics results

Table order determines the primary local F-012 result. Retain every
independently determinable secondary failure in order, with ordinal field-name
ordering for ties. Missing whole dependency objects use dependency reasons;
inconsistent supplied bindings use `IDENTITY_INVALID`. Blocked enabled gates
are `UNAVAILABLE`; validated disabled gates remain `NOT_APPLICABLE`.

| Priority | Condition | Local result / reason |
|---:|---|---|
| 1 | Invalid/missing required identity within supplied evidence; conflicting digest, direction, version, unit, profile or provenance binding | `UNAVAILABLE / IDENTITY_INVALID` |
| 2 | Missing/invalid pinned configuration, invalid enabled flag, or missing/malformed/nonfinite enabled threshold | `UNAVAILABLE / CONFIG_INVALID` |
| 3 | Missing/unusable dependency or missing/malformed/nonfinite/nonpositive required output | `UNAVAILABLE / DEPENDENCY_ENTRY_UNAVAILABLE`, then `DEPENDENCY_STOP_UNAVAILABLE`, then `DEPENDENCY_TP_UNAVAILABLE`, then `DEPENDENCY_SIZING_UNAVAILABLE`; retain upstream reasons |
| 4 | Required arithmetic failure, `N != Q*E`, or inconsistent required exact/report/output invariant | `UNAVAILABLE / NUMERIC_INVARIANT_VIOLATION` |
| 5 | Valid positive Entry and Stop coincide: `dr = 0` | `FAIL / ZERO_RISK_DISTANCE`; R:R is unavailable, never divided |
| 6 | Otherwise `dr < 0` or `dw <= 0` | `FAIL / INVALID_GEOMETRY`; enabled economic gates are unavailable |
| 7 | Required maker/taker fact or required fee provenance is absent/unavailable | `UNAVAILABLE / MISSING_EXCHANGE_FACT`, identifying the fee field |
| 8 | Supplied fee is malformed/nonfinite, has unsupported units, or fails established applicability; binding conflicts already use priority 1 | `UNAVAILABLE / INVALID_EXCHANGE_FACT` |
| 9 | Applicable additional cost lacks the separately approved deterministic definition/integration required above | `UNAVAILABLE / COST_POLICY_UNAVAILABLE` |
| 10 | Evaluable enabled gross R:R comparison fails | `FAIL / RR_BELOW_MINIMUM` |
| 11 | Evaluable enabled net-edge comparison fails | `FAIL / NET_EDGE_BELOW_MINIMUM` |

With no failures:

```text
PASS / AVAILABLE
```

Any overall non-PASS result prevents successful construction and approved /
actionable economics. Available values remain diagnostic.

These formula-local ordered outcomes coexist with the original S-003
stage/global aggregation above. Initial capital-dependent gates remain
NOT_YET_EVALUATED. Validated disabled gates remain NOT_APPLICABLE but never
waive independently required dependencies, geometry, identity or economics.
No local reason table creates a second initial approval or a new wire enum.

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

**F-009 local reasons.** Preserve the existing generic/global vocabulary. The formula-local mapping is:

| Condition | Reason |
|---|---|
| invalid stop-loss mode | `CONFIG_INVALID` |
| FIXED mode missing `fixed_sl_pct` | `CONFIG_INVALID` |
| malformed, nonfinite or nonpositive `fixed_sl_pct` | `CONFIG_INVALID` |
| LONG FIXED `fixed_sl_pct >= 100` | `CONFIG_INVALID` |
| missing, nonfinite or nonpositive Entry | `DEPENDENCY_ENTRY_UNAVAILABLE` or source-specific entry reason |
| missing, nonfinite or nonpositive tick size | `MISSING_EXCHANGE_FACT` |
| arithmetic failure or invalid fixed rounded stop | `ROUNDING_ERROR` |
| dynamic branch unavailable | `SL_UNAVAILABLE` with original branch `dependency_reason` |
| dynamic branch identity/provenance mismatch | `SL_UNAVAILABLE` or `IDENTITY_INVALID`, preserving mismatch diagnostics |

The branch `dependency_reason` is retained; these local results do not rename unrelated S-003 outcomes or wire enums.

**F-010 local reasons.** Apply the exact primary sequence in Part IV §24 and retain secondary diagnostics. The local conditions are:

| Condition | Reason |
|---|---|
| invalid/missing TP mode/configuration | `CONFIG_INVALID` |
| invalid F-008/handoff identity, digest, provenance, duplicate/conflicting IDs or invalid binding | `IDENTITY_INVALID` |
| `E` missing or `<= 0` | `MISSING_ENTRY_REFERENCE` |
| `A` missing or `<= 0` | `MISSING_ATR` |
| `t` missing or `<= 0` | `MISSING_TICK_SIZE` |
| `set_family` missing/invalid | `MISSING_SET_FAMILY` |
| thesis policy missing/invalid | `MISSING_THESIS_REFERENCE_POLICY` |
| `reference_geometry.levels` unavailable/unusable, or usable but no governed directionally permitted levels for the active direction/family | `NO_FAVORABLE_SIDE_GEOMETRY` |
| required thesis reference invalid after valid handoff primitives | `THESIS_REFERENCE_INVALID` |
| directional_pool non-empty but zero strict favorable-side references | `NO_ELIGIBLE_REFERENCE` |
| no reachable target after allowed too-close skips | `NO_REACHABLE_TARGET` |
| next traversed candidate too far | `TARGET_TOO_FAR` |
| inward rounding makes target too close | `TARGET_TOO_CLOSE_AFTER_ROUNDING` |
| arithmetic or rounded-output invariant failure | `ROUNDING_ERROR` |

### F-011 local reason vocabulary

The F-011 table in §43 governs its local primary/secondary outcome order and
spelling. It does not replace unrelated generic/global S-003 codes or wire
enums. Retain upstream dependency reasons.

```text
IDENTITY_INVALID
CONFIG_INVALID
INVALID_CAPITAL_GRANT
DEPENDENCY_ENTRY_UNAVAILABLE
DEPENDENCY_STOP_UNAVAILABLE
DEPENDENCY_TP_UNAVAILABLE
INVALID_LEVERAGE
MISSING_EXCHANGE_FACT
INVALID_EXCHANGE_FACT
MAX_ORDER_QTY_UNAVAILABLE
LEVERAGE_ABOVE_MAXIMUM
NUMERIC_INVARIANT_VIOLATION
CAPITAL_BOUND_VIOLATION
QTY_ZERO_AFTER_FLOOR
QTY_BELOW_MINIMUM
QTY_ABOVE_MAXIMUM
NOTIONAL_BELOW_MINIMUM
AVAILABLE
```

### F-012 local reason vocabulary

Use §43's exact local precedence and preserve upstream reasons. STOP in
DEPENDENCY_STOP_UNAVAILABLE is the certified local spelling; do not rename
unrelated legacy/global SL reason codes.

```text
IDENTITY_INVALID
CONFIG_INVALID
DEPENDENCY_ENTRY_UNAVAILABLE
DEPENDENCY_STOP_UNAVAILABLE
DEPENDENCY_TP_UNAVAILABLE
DEPENDENCY_SIZING_UNAVAILABLE
NUMERIC_INVARIANT_VIOLATION
ZERO_RISK_DISTANCE
INVALID_GEOMETRY
MISSING_EXCHANGE_FACT
INVALID_EXCHANGE_FACT
COST_POLICY_UNAVAILABLE
RR_BELOW_MINIMUM
NET_EDGE_BELOW_MINIMUM
AVAILABLE
```

NONPOSITIVE_NET_LOSS_SL is an optional diagnostic reason with null net_rr, not
a new mandatory construction rejection. Generic S-003/global codes and existing
wire enums remain unchanged.

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

LONG permits only:

```text
SWING_LOW_15M
SWING_LOW_1H
PREVIOUS_DAY_LOW
RANGE_LOW
```

SHORT permits only:

```text
SWING_HIGH_15M
SWING_HIGH_1H
PREVIOUS_DAY_HIGH
RANGE_HIGH
```

These restrictions apply to both thesis overrides and default candidates. A price-side test does not admit a wrong structural type. BREAKOUT_RECLAIM adds no implicit high-to-support or low-to-resistance conversion.

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

**F-008 preflight precedes every policy branch.** Consume a valid committed LONG/SHORT Market Handoff for the same `decision_cycle_id`, `set_result_id`, immutable handoff digest and pinned Position configuration. Invalid contract identity, direction, provenance or required structure terminates handoff consumption before selection; it is not a fallback warning. Non-null thesis references require unique exact IDs and consistent originating role, occurrence, type, timeframe and price evidence. Missing/conflicting origin bindings, dangling or duplicate IDs and producer availability violations reject the handoff before any REQUIRED/PREFERRED/NONE branch. Preserve the original producer reference even when it fails calculation eligibility; a selected calculation reference is not a new producer binding.

`NONE` requires both `entry_context.thesis_reference_level_id` and its originating binding to be null. A contract-valid PREFERRED null pair is permitted. For REQUIRED, absent or calculation-ineligible thesis evidence has no fallback and yields `THESIS_ENTRY_REFERENCE_INVALID` after the binding preflight.

The match reference S, received Q18 ATR A and tick t must be finite and strictly positive; family and policy must be valid. Defensive missing/malformed/nonfinite/nonpositive primitive diagnostics have this primary order:

```text
MISSING_SET_MATCH_REFERENCE
MISSING_ATR
MISSING_TICK_SIZE
MISSING_SET_FAMILY
MISSING_THESIS_REFERENCE_POLICY
```

Retain all known failures; diagnostics do not authorize an invalid handoff. References must have positive finite prices, an approved directional type and exact availability as-of `matched_at`. Strict side improvement and the inclusive raw 0.10–1.25 ATR band precede default ranking. Threshold checks use exact arithmetic, equivalently `10*d >= A` and `4*d <= 5*A`; no extra quantizer, epsilon or recovered ATR precision is permitted.

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

Only after §12 producer/binding preflight, a contract-valid null pair or a valid-bound reference failing F-008 type/side/raw-depth eligibility (including TOO_SHALLOW or TOO_DEEP) uses:

```text
warning = INVALID_THESIS_ENTRY_REFERENCE
continue with default candidate pool
```

The preferred thesis reference does not terminate the default pool when it is outside the admissibility band.

A missing, dangling, duplicate, conflicting or producer-future binding is a handoff rejection, never this warning/fallback branch. Once a reference is selected, any rounding or rounded-band failure is terminal, including PREFERRED; no alternate-reference retry is permitted.

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
3. ascending case-sensitive ordinal Unicode code-point level_id (shorter prefix first)
```

`age_seconds` is diagnostic only.

Use exact `available_at`, not integer `age_seconds`; neither input array order nor locale-sensitive collation participates.

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

For default selection, the base pool contains positive finite, approved directionally typed references with exact availability as-of `matched_at`, before strict improvement and depth checks. Use:

```text
empty base pool
    -> NO_ELIGIBLE_ENTRY_REFERENCE
nonempty base pool with no strictly improving reference
    -> NO_ENTRY_SIDE_GEOMETRY
improving references but none inside the inclusive raw ATR band
    -> NO_ADMISSIBLE_ENTRY_DEPTH
```

REQUIRED thesis eligibility failure takes precedence over these pool-exhaustion reasons. Preserve reference exclusions and genuine PREFERRED fallback warnings; no raw-ineligible reference can be rescued by rounding.

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

Before recomputing depth, require the selected-reference rounding to satisfy:

```text
finite rounded_entry_price > 0
rounded_entry_price / tick_size is an integer
LONG: rounded_entry_price = floor(selected_reference_price / tick_size) * tick_size
      rounded_entry_price < set_match_reference_price
SHORT: rounded_entry_price = ceil(selected_reference_price / tick_size) * tick_size
       rounded_entry_price > set_match_reference_price
```

Arithmetic failure or failed positivity/grid/correct-outward-rounding/strict-side invariants yields `ROUNDING_ERROR`. Invalid input tick belongs to §12 input rejection. No usable entry price may be exposed after a failure.

Then recompute:

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

Any selected-reference rounding or rounded-band failure is terminal: no alternative reference, clamp, offset or repricing, including under PREFERRED. Diagnostic prices remain non-actionable.

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

apply §12 preflight before selection:
    valid same-bound committed LONG handoff/configuration and immutable producer evidence
    finite positive M, received A and tick; valid family/policy
    reject invalid/dangling/duplicate/conflicting/producer-future bindings
    NONE requires thesis ID and binding both null
then validate REQUIRED/PREFERRED/NONE thesis policy

build LONG base pool before side/depth filtering:
    positive finite prices, §8 permitted LOW types only,
    exact availability as-of matched_at; same restrictions apply to thesis
build default structural ordering using:
hierarchy_for(entry_context.set_family)

where the canonical family tables in Sections 16–19 are authoritative; for RANGE this starts with RANGE_LOW.

for every base-pool reference (exclude non-improving side before depth):
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
        THESIS_ENTRY_REFERENCE_INVALID; terminate
    else:
        select it

PREFERRED thesis reference:
    if valid-bound and ELIGIBLE:
        select it
    else if contract-valid null pair or valid-bound calculation ineligibility:
        INVALID_THESIS_ENTRY_REFERENCE warning + use default ELIGIBLE pool
    binding errors already terminated in preflight

default pool only if no thesis reference was selected (NONE or permitted PREFERRED fallback):
    if zero base-pool refs:
        NO_ELIGIBLE_ENTRY_REFERENCE; terminate

    if base pool nonempty but no reference.price < M:
        NO_ENTRY_SIDE_GEOMETRY; terminate

    if improving references exist but zero ELIGIBLE refs:
        NO_ADMISSIBLE_ENTRY_DEPTH; terminate

    select highest structural-priority ELIGIBLE ref
    within type: latest exact available_at, smallest raw improvement distance,
                 ascending case-sensitive Unicode code-point level_id

raw_entry = selected reference price
rounded_entry = floor(raw_entry / tick) × tick

before success require finite positive rounded_entry, exact tick grid,
    rounded_entry = floor(raw_entry / tick) * tick,
    rounded_entry < M
arithmetic or invariant failure -> ROUNDING_ERROR; terminate

recompute rounded improvement:
    < 0.10 → ENTRY_TOO_SHALLOW_AFTER_ROUNDING
    > 1.25 → ENTRY_TOO_DEEP_AFTER_ROUNDING

Any selected-reference rounding/band failure terminates without another reference,
including PREFERRED. Failed diagnostic prices are non-actionable.

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

apply §12 preflight before selection:
    valid same-bound committed SHORT handoff/configuration and immutable producer evidence
    finite positive M, received A and tick; valid family/policy
    reject invalid/dangling/duplicate/conflicting/producer-future bindings
    NONE requires thesis ID and binding both null
then validate REQUIRED/PREFERRED/NONE thesis policy

build SHORT base pool before side/depth filtering:
    positive finite prices, §8 permitted HIGH types only,
    exact availability as-of matched_at; same restrictions apply to thesis
build default structural ordering using:
hierarchy_for(entry_context.set_family)

where the canonical family tables in Sections 16–19 are authoritative; for RANGE this starts with RANGE_HIGH.

for every base-pool reference (exclude non-improving side before depth):
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
        THESIS_ENTRY_REFERENCE_INVALID; terminate
    else:
        select it

PREFERRED thesis reference:
    if valid-bound and ELIGIBLE:
        select it
    else if contract-valid null pair or valid-bound calculation ineligibility:
        INVALID_THESIS_ENTRY_REFERENCE warning + use default ELIGIBLE pool
    binding errors already terminated in preflight

default pool only if no thesis reference was selected (NONE or permitted PREFERRED fallback):
    if zero base-pool refs:
        NO_ELIGIBLE_ENTRY_REFERENCE; terminate

    if base pool nonempty but no reference.price > M:
        NO_ENTRY_SIDE_GEOMETRY; terminate

    if improving references exist but zero ELIGIBLE refs:
        NO_ADMISSIBLE_ENTRY_DEPTH; terminate

    select highest structural-priority ELIGIBLE ref
    within type: latest exact available_at, smallest raw improvement distance,
                 ascending case-sensitive Unicode code-point level_id

raw_entry = selected reference price
rounded_entry = ceil(raw_entry / tick) × tick

before success require finite positive rounded_entry, exact tick grid,
    rounded_entry = ceil(raw_entry / tick) * tick,
    rounded_entry > M
arithmetic or invariant failure -> ROUNDING_ERROR; terminate

recompute rounded improvement:
    < 0.10 → ENTRY_TOO_SHALLOW_AFTER_ROUNDING
    > 1.25 → ENTRY_TOO_DEEP_AFTER_ROUNDING

Any selected-reference rounding/band failure terminates without another reference,
including PREFERRED. Failed diagnostic prices are non-actionable.

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

LONG permits only:

```text
SWING_LOW_15M
SWING_LOW_1H
PREVIOUS_DAY_LOW
RANGE_LOW
```

SHORT permits only:

```text
SWING_HIGH_15M
SWING_HIGH_1H
PREVIOUS_DAY_HIGH
RANGE_HIGH
```

These sets apply to thesis and fallback references. Preserve strict adverse-side eligibility against the final F-008 Entry: LONG `r < E - t`, SHORT `r > E + t`. No cached Set side, wrong-type reference or synthetic level can replace these tests.

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

**F-006/F-007 preflight before reference selection.** Require a valid immutable handoff identity/digest/provenance, same cycle/result/instrument/direction, pinned Position configuration and same-bound AVAILABLE F-008 planned Entry. Entry E, received Q18 ATR A and tick t must be finite and strictly positive; family and thesis policy must be valid. Do not recompute or recover hidden ATR precision. Existing missing-Entry/ATR/tick/family/policy reasons remain.

Reject invalid/conflicting producer bindings, dangling thesis IDs, producer availability violations, duplicate/conflicting canonical level IDs and a NONE policy with either non-null thesis ID or non-null origin binding. These are handoff-consumption failures, not warning-only fallback. Candidate prices must be finite and positive, IDs unique, exact `available_at <= matched_at`, types directionally permitted by §6, and price strictly beyond the one-tick adverse boundary against E.

REQUIRED has no fallback; invalid required thesis evidence yields `usable=false`, `THESIS_REFERENCE_INVALID`, without downgrading the handoff-integrity preflight. PREFERRED fallback is limited to a contract-valid null pair or a valid-bound reference failing the directional stop's calculation eligibility. NONE requires both fields null before default ranking. If a producer reference shared with Entry fails stop-side geometry, retain the original producer binding; calculation fallback never rebinds or rewrites it.

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

Only after §10 producer/binding preflight, if the pair is contract-valid null or a valid-bound reference fails F-006/F-007 calculation eligibility:

```text
add warning = INVALID_THESIS_REFERENCE_OVERRIDE
continue to default hierarchy
```

Invalid, dangling, conflicting, duplicate or producer-future bindings reject before this branch. Once a reference is selected, width or rounding failure is terminal, not another PREFERRED fallback; REQUIRED remains no-fallback.

---

# 13. Thesis-reference NONE

If:

```text
policy = NONE
```

then:

```text
thesis_reference_level_id must be null
origin_binding must be null
```

and default reference ranking is used.

If either the thesis ID or its origin binding is non-null with `NONE`, reject the invalid handoff/policy binding before selection under §10. This is not a successful-path warning and does not authorize default ranking.

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
3. ascending case-sensitive ordinal Unicode code-point level_id (shorter prefix first)
```

`age_seconds` is diagnostic only and is not a separate ranking criterion because it is derived from `available_at`.

Use exact `available_at` and exact adverse distance (LONG `E - r`, SHORT `r - E`). No array order, locale collation, case folding, natural sort or numeric-substring sorting can decide the ID tie.

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

The persisted flag is defined by the strict comparison:

```text
LONG:  minimum_distance_adjustment_applied = (raw_stop > minimum_stop)
SHORT: minimum_distance_adjustment_applied = (raw_stop < minimum_stop)
```

Equality means `false`; it is not an adjustment. The min/max formulas and 0.20/0.50/2.00 ATR constants remain unchanged.

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

Before a usable stop is exposed, also require:

```text
rounded_stop is finite and > 0
rounded_stop / tick_size is an integer
LONG: rounded_stop = floor(adjusted_stop / tick_size) * tick_size
SHORT: rounded_stop = ceil(adjusted_stop / tick_size) * tick_size
```

Arithmetic failure or violation of any positivity/grid/correct-outward-rounding/reference-side/Entry-side invariant yields `usable=false`, `ROUNDING_ERROR`. Diagnostic raw/rounded prices may be retained but are non-actionable. Both the pre-rounding and post-rounding risk-price bounds remain inclusive `<= 2.00 * ATR_15m`; exceeding either is `SL_TOO_WIDE`. No clamp, offset, inward correction, weaker-reference retry, ATR-only fallback, Entry repricing or exchange-specific repair is permitted.

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
Require §10 same-bound F-008/handoff/configuration and producer-binding preflight.
Select a §6 directionally permitted LOW reference under §§11–20;
reference must be strictly below E - tick.
Use exact recency/adverse-distance/Unicode ID order; no binding repair.
E, received A and tick must be finite and positive.

R = selected adverse reference
A = ATR_15m
E = planned entry

raw_stop = R - 0.20A
minimum_stop = E - 0.50A
adjusted_stop = min(raw_stop, minimum_stop)
minimum_distance_adjustment_applied = (raw_stop > minimum_stop)

pre_risk_atr = (E - adjusted_stop)/A
if pre_risk_atr > 2.0:
    usable = false; reason = SL_TOO_WIDE; terminate

rounded_stop = floor(adjusted_stop/tick)×tick

require finite rounded_stop > 0 and integer rounded_stop/tick
require rounded_stop = floor(adjusted_stop/tick)×tick
require rounded_stop < R and rounded_stop < E
arithmetic or invariant failure:
    usable = false; reason = ROUNDING_ERROR; terminate

post_risk_atr = (E - rounded_stop)/A
if post_risk_atr > 2.0:
    usable = false; reason = SL_TOO_WIDE; terminate

Only after all checks pass:
    usable = true; reason = AVAILABLE
    rounded_stop_price = rounded_stop
No weaker-reference retry after width or rounding failure; failed prices are non-actionable.
```

---

# 38. SHORT formula

```text
Require §10 same-bound F-008/handoff/configuration and producer-binding preflight.
Select a §6 directionally permitted HIGH reference under §§11–20;
reference must be strictly above E + tick.
Use exact recency/adverse-distance/Unicode ID order; no binding repair.
E, received A and tick must be finite and positive.

R = selected adverse reference
A = ATR_15m
E = planned entry

raw_stop = R + 0.20A
minimum_stop = E + 0.50A
adjusted_stop = max(raw_stop, minimum_stop)
minimum_distance_adjustment_applied = (raw_stop < minimum_stop)

pre_risk_atr = (adjusted_stop - E)/A
if pre_risk_atr > 2.0:
    usable = false; reason = SL_TOO_WIDE; terminate

rounded_stop = ceil(adjusted_stop/tick)×tick

require finite rounded_stop > 0 and integer rounded_stop/tick
require rounded_stop = ceil(adjusted_stop/tick)×tick
require rounded_stop > R and rounded_stop > E
arithmetic or invariant failure:
    usable = false; reason = ROUNDING_ERROR; terminate

post_risk_atr = (rounded_stop - E)/A
if post_risk_atr > 2.0:
    usable = false; reason = SL_TOO_WIDE; terminate

Only after all checks pass:
    usable = true; reason = AVAILABLE
    rounded_stop_price = rounded_stop
No weaker-reference retry after width or rounding failure; failed prices are non-actionable.
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

LONG default and thesis targets permit only:

```text
SWING_HIGH_15M
SWING_HIGH_1H
PREVIOUS_DAY_HIGH
RANGE_HIGH
```

SHORT default and thesis targets permit only:

```text
SWING_LOW_15M
SWING_LOW_1H
PREVIOUS_DAY_LOW
RANGE_LOW
```

A wrong structural type is not admitted by price-side geometry. No opposite-type conversion is inferred.

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

**F-010 preflight precedes thesis/default selection.** The pinned TP mode must be DYNAMIC with a valid Position configuration ID/version/content digest; missing/invalid mode or configuration is `CONFIG_INVALID`. Consume an AVAILABLE F-008 Entry bound to the same instrument, immutable direction, decision cycle/result, Market Handoff identity/digest and tick provenance. Require valid handoff/F-008 provenance, instrument metadata revision, `tp_context.set_family` and thesis policy; E, received Q18 ATR A and tick t must be finite and strictly positive. Preserve Q18 ATR without recomputation or hidden-precision recovery.

Reject invalid/conflicting producer bindings, dangling thesis IDs, producer availability violations and duplicate/conflicting canonical level IDs before fallback. With NONE, both thesis ID and origin binding must be null. These are identity/configuration/dependency failures, never warning-only fallback cases. Preserve original producer bindings separately from selected calculation targets.

PREFERRED fallback is allowed only for a contract-valid null pair or a valid-bound reference failing F-010 calculation eligibility. REQUIRED has no fallback; required thesis absence or failed type/price/as-of/strict-side/reachability eligibility returns `usable=false`, `THESIS_REFERENCE_INVALID` after higher-precedence preflight/geometry checks. Apply the exact local precedence in §24; do not downgrade an identity failure into a thesis warning. F-010 adds no geometry field or current-market query.

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

Only after §10 preflight, if the pair is contract-valid null or a valid-bound target fails F-010 calculation eligibility, including the reachability band:

```text
warning = INVALID_THESIS_REFERENCE_OVERRIDE
continue with default target hierarchy
```

Malformed, conflicting, duplicate, dangling or producer-future bindings reject before this branch. This is preselection fallback only. Once a target is selected, every rounding or post-rounding failure is terminal, including PREFERRED; no lower-priority target, Entry repricing or synthesized target is permitted.

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
3. ascending case-sensitive ordinal Unicode code-point level_id, with shorter prefixes first
```

`age_seconds` remains diagnostic only.

Use exact `available_at` and exact favorable distance. No locale collation, normalization, case folding, natural sort, numeric-substring sort, array order or arrival order is permitted. A TOO_FAR candidate terminates before every later candidate, including an older one of the same type. PREFERRED preselection fallback does not reorder default traversal.

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

F-010 introduces no additional geometry dependency and no field outside Market
Handoff v4. Geometry capability is derived only from the frozen
`reference_geometry.levels` collection denoted in calculation notation as
`references.levels[]`.

The `reference_geometry.levels` collection is usable only when it is present in
the frozen handoff, schema-valid under the handoff version, bound to the same
handoff identity/digest, and replayable from the persisted handoff snapshot. A
missing, null, non-array, schema-invalid, unbound or non-replayable collection is
not silently treated as an empty set; after higher-precedence identity and
missing-primitive checks, it returns:

```text
usable = false
reason = NO_FAVORABLE_SIDE_GEOMETRY
```

Define:

```text
directional_pool =
  governed levels in references.levels[]
  with level_type in the active direction's permitted target type set
  and finite positive price
  and available_at <= matched_at
```

If the collection is usable but `directional_pool` is empty, F-010 has no
governed favorable-side geometry capability for the active direction/family and
returns:

```text
usable = false
reason = NO_FAVORABLE_SIDE_GEOMETRY
```

The `basic_pool` is the subset of `directional_pool` that also passes Part IV §7 strict favorable-side price geometry for the active direction.

If `directional_pool` is non-empty and `basic_pool` is empty:

```text
usable = false
reason = NO_ELIGIBLE_REFERENCE
```

The `traversable_pool` is the ordered subset of `basic_pool` whose level type
appears in the active Set-family directional hierarchy. If the basic pool is
non-empty but no basic eligible levels belong to the active hierarchy:

```text
usable = false
reason = NO_REACHABLE_TARGET
```

and preserve diagnostics showing the non-traversable basic eligible levels.

## `NO_FAVORABLE_SIDE_GEOMETRY`

Use when the frozen collection is unusable or its governed directional pool is empty, after the higher-precedence configuration/identity/primitive checks. No separate upstream capability field is required.

## `NO_ELIGIBLE_REFERENCE`

Use when the directional pool is nonempty but its basic pool is empty under strict favorable-side geometry relative to the final F-008 `planned_entry_reference`, subject to REQUIRED thesis precedence.

## `NO_REACHABLE_TARGET`

Use when the basic pool is nonempty but its traversable pool is empty, preserving non-traversable-level diagnostics; or when the default structural hierarchy exhausts only TOO_CLOSE traversed candidates without selecting a target or encountering TOO_FAR.

## `TARGET_TOO_FAR`

Use when, after any allowed `TOO_CLOSE` skips, the next structurally traversed candidate has:

```text
distance_atr > 4.00
```

Selection terminates immediately.

Primary reason precedence:

```text
1. CONFIG_INVALID
   - invalid or missing pinned TP mode/configuration

2. IDENTITY_INVALID
   - invalid handoff/F-008 identity, digest, provenance or binding consistency

3. missing primitive reasons
   MISSING_ENTRY_REFERENCE
   MISSING_ATR
   MISSING_TICK_SIZE
   MISSING_SET_FAMILY
   MISSING_THESIS_REFERENCE_POLICY

4. NO_FAVORABLE_SIDE_GEOMETRY
   - reference_geometry.levels unavailable/unusable, or usable but no governed
     directionally permitted level exists for the active direction/family

5. THESIS_REFERENCE_INVALID
   - REQUIRED thesis reference missing or invalid after valid handoff primitives

6. NO_ELIGIBLE_REFERENCE
   - directional_pool non-empty but zero levels pass strict favorable-side
     price geometry

7. traversal outcomes
   TARGET_TOO_FAR
   NO_REACHABLE_TARGET
   TARGET_TOO_CLOSE_AFTER_ROUNDING
   ROUNDING_ERROR
   AVAILABLE
```

Secondary diagnostics must preserve all discovered contributing conditions.

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

Before exposing a usable target, also require:

```text
rounded_tp is finite and > 0
rounded_tp / tick_size is an integer
LONG: rounded_tp = floor(selected_target_price / tick_size) * tick_size
SHORT: rounded_tp = ceil(selected_target_price / tick_size) * tick_size
```

Together with the Entry/target-side checks above, any arithmetic or positivity/grid/correct-inward-rounding/geometry failure yields `usable=false`, `ROUNDING_ERROR`. Failed prices are non-actionable. Let `rounded_distance_price = abs(rounded_tp - planned_entry_reference)`; require `4 * rounded_distance_price >= 3 * ATR_15m` and `rounded_distance_price <= 4 * ATR_15m`. The lower failure is `TARGET_TOO_CLOSE_AFTER_ROUNDING`; the upper failure is `ROUNDING_ERROR`. These are the existing inclusive 0.75/4.00 ATR post-round bounds. Failure is terminal under all policies, including PREFERRED: no alternative target, Entry repricing, SL-distance target or ATR-only repair.

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

After final construction, F-012 evaluates planned fee-aware R:R/net edge
using frozen factual signed maker/taker rates and the final prices/quantity.
Its additional deterministic-cost baseline is empty; an asserted applicable
extra cost without separately approved definition/integration is
COST_POLICY_UNAVAILABLE. This creates no live spread/slippage gate and inserts
no research assumptions or planned funding. Planned edge is eligibility, not
proof of profitability.

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
    reference_geometry_collection_status:
    directional_candidate_level_ids: []
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
    unvisited_level_ids: []

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

The collection/pool/traversal fields are Position-local diagnostics, not new Market Handoff or Order Spec fields. Optional traversal after primary selection must be marked diagnostic and cannot change the selected target, primary reason or feasibility. Preserve unvisited IDs rather than pretending that primary traversal visited them.

---

# 45. LONG algorithm

```text
E = planned entry
A = ATR_15m

Apply §10 preflight and §24 exact reason precedence:
    valid pinned DYNAMIC configuration, same-bound AVAILABLE F-008 and handoff
    valid immutable identity/digest/provenance/producer binding; NONE is a null pair
    finite positive E, received A and tick; valid family/policy
    reject unusable frozen collection or empty HIGH-type directional_pool
        as NO_FAVORABLE_SIDE_GEOMETRY after higher-precedence checks
Build basic_pool using strict r > E + tick; derive traversable_pool under frozen family hierarchy.
REQUIRED: valid-bound eligible/reachable thesis selects; otherwise THESIS_REFERENCE_INVALID.
PREFERRED: valid-bound eligible/reachable thesis selects; contract-valid null or
           valid-bound calculation failure warns INVALID_THESIS_REFERENCE_OVERRIDE
           and proceeds to default traversal. Binding errors never fall back.
If no thesis target selected:
    nonempty directional_pool with empty basic_pool -> NO_ELIGIBLE_REFERENCE
    nonempty basic_pool with empty traversable_pool -> NO_REACHABLE_TARGET
Default traversal occurs only when no thesis target has selected.
Order by family priority, latest exact available_at, smallest exact favorable distance,
then ascending case-sensitive Unicode code-point ID (shorter prefix first).
A latest same-type TOO_FAR terminates before older same-type candidates.

for target in LONG structural priority order, only if no thesis target selected:
    if target not in traversable_pool:
        preserve exclusion/non-traversable diagnostic
        continue

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

No-target and TOO_FAR outcomes above terminate without constructing a price.
If no target selected after default traversal and no TOO_FAR termination:
    NO_REACHABLE_TARGET; terminate

raw_tp = selected target price
rounded_tp = floor(raw_tp/tick)×tick

require finite rounded_tp > 0 and integer rounded_tp/tick
require rounded_tp = floor(raw_tp/tick)×tick
require rounded_tp > E and rounded_tp <= raw_tp
arithmetic or invariant failure -> ROUNDING_ERROR; terminate

recompute rounded_distance_price = abs(rounded_tp - E)

if 4 * rounded_distance_price < 3 * A:
    TARGET_TOO_CLOSE_AFTER_ROUNDING; terminate
elif rounded_distance_price > 4 * A:
    ROUNDING_ERROR; terminate
else:
    AVAILABLE

All raw and rounded comparisons are exact; ratio displays never decide eligibility.
No selected-reference post-round failure retries another target, including PREFERRED.
Optional alternative traversal is diagnostic only and cannot change selection/reason.
```

---

# 46. SHORT algorithm

```text
E = planned entry
A = ATR_15m

Apply §10 preflight and §24 exact reason precedence:
    valid pinned DYNAMIC configuration, same-bound AVAILABLE F-008 and handoff
    valid immutable identity/digest/provenance/producer binding; NONE is a null pair
    finite positive E, received A and tick; valid family/policy
    reject unusable frozen collection or empty LOW-type directional_pool
        as NO_FAVORABLE_SIDE_GEOMETRY after higher-precedence checks
Build basic_pool using strict r < E - tick; derive traversable_pool under frozen family hierarchy.
REQUIRED: valid-bound eligible/reachable thesis selects; otherwise THESIS_REFERENCE_INVALID.
PREFERRED: valid-bound eligible/reachable thesis selects; contract-valid null or
           valid-bound calculation failure warns INVALID_THESIS_REFERENCE_OVERRIDE
           and proceeds to default traversal. Binding errors never fall back.
If no thesis target selected:
    nonempty directional_pool with empty basic_pool -> NO_ELIGIBLE_REFERENCE
    nonempty basic_pool with empty traversable_pool -> NO_REACHABLE_TARGET
Default traversal occurs only when no thesis target has selected.
Order by family priority, latest exact available_at, smallest exact favorable distance,
then ascending case-sensitive Unicode code-point ID (shorter prefix first).
A latest same-type TOO_FAR terminates before older same-type candidates.

for target in SHORT structural priority order, only if no thesis target selected:
    if target not in traversable_pool:
        preserve exclusion/non-traversable diagnostic
        continue

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

No-target and TOO_FAR outcomes above terminate without constructing a price.
If no target selected after default traversal and no TOO_FAR termination:
    NO_REACHABLE_TARGET; terminate

raw_tp = selected target price
rounded_tp = ceil(raw_tp/tick)×tick

require finite rounded_tp > 0 and integer rounded_tp/tick
require rounded_tp = ceil(raw_tp/tick)×tick
require rounded_tp < E and rounded_tp >= raw_tp
arithmetic or invariant failure -> ROUNDING_ERROR; terminate

recompute rounded_distance_price = abs(rounded_tp - E)

if 4 * rounded_distance_price < 3 * A:
    TARGET_TOO_CLOSE_AFTER_ROUNDING; terminate
elif rounded_distance_price > 4 * A:
    ROUNDING_ERROR; terminate
else:
    AVAILABLE

All raw and rounded comparisons are exact; ratio displays never decide eligibility.
No selected-reference post-round failure retries another target, including PREFERRED.
Optional alternative traversal is diagnostic only and cannot change selection/reason.
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
