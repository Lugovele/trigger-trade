# TriggerTrade — Portfolio Rules Methodology

**File:** `PORTFOLIO_RULES.md`  
**Version:** 1.2.15
**Architecture role:** `Portfolio Rules — Capital Management`


**Shared normative protocols:** `../SYSTEM_PROTOCOLS.md` (P1–P17). **ID ownership:** `../IDENTIFIER_LINEAGE.md`. Generated wire-shape illustrations use the strict schema registry in `../schemas/`; nullable annotations are not literal payload objects.

## Purpose

This is the single canonical methodology document for the TriggerTrade **Portfolio Rules** block.

It consolidates the previously approved Portfolio Rules methodology while synchronizing it with the final four-block architecture.

Canonical external flows:

```text
Portfolio Rules → Set
Coins: OPEN / CLOSE

Portfolio Rules → Position Rules
Capital and Limits

Position Rules → Portfolio Rules
Approve / Reject

Portfolio Rules → Order Lifecycle
Submit Authorized

Order Lifecycle → Portfolio Rules
Order Event

Portfolio Rules ↔ API
Portfolio Data Request
```

Portfolio Rules owns:
- own-capital accounting;
- portfolio limits;
- coin allocations;
- tranche sizing;
- active analysis need (`OPEN / CLOSE`);
- `SUBMISSION_HOLD`;
- `Submit Authorized` after successful hold;
- reservation/free/filled accounting;
- daily loss gating;
- cooldown;
- API-backed portfolio state synchronization.

Portfolio Rules does not:
- analyze the market;
- determine direction;
- calculate Entry / SL / TP;
- choose leverage;
- construct the final Order Spec;
- manage exchange order mechanics.

`decision_cycle_id` is **not created by Portfolio Rules**.

Portfolio Rules learns it from `Approve / Reject` and stores it from the initial decision; only after APPROVE may it create a grant bound to that exact opportunity.

---

# Part I — Capital Model and Portfolio Rules

# 1. Purpose

Portfolio Rules is the TriggerTrade **Capital Management** block.

It answers:

```text
1. Which symbols currently have an OPEN need for new-opportunity analysis?

2. How much own portfolio capital is currently available for the next logical tranche?

3. After Position Rules returns APPROVE / REJECT,
   whether to issue the approved opportunity a grant, and after construction whether current capacity can be held?

4. After Order Lifecycle events,
   what is the current authoritative portfolio state?
```

Portfolio Rules does not:
- analyze the market;
- determine direction;
- calculate Entry;
- calculate Stop Loss;
- calculate Take Profit;
- choose leverage;
- build exchange order economics.

Those belong to Set and Position Rules.

---

# 2. Core accounting unit

Portfolio Rules uses only:

```text
OWN COMMITTED CAPITAL
```

It does not use leveraged order notional for allocation management.

Canonical distinction:

```text
requested_capital_per_tranche
= own portfolio capital allocated to one logical tranche

target_order_notional
= Position Rules derived market exposure after leverage
```

Example:

```text
requested_capital_per_tranche = $250
leverage = 5x

Portfolio Rules counts = $250
Position Rules may produce order notional ≈ $1,250
```

---

# 3. Daily accounting boundary

All daily Portfolio Rules calculations use one accounting day.

Canonical baseline:

```text
timezone = Israel local time
rollover = 00:00 Israel local time
```

At rollover:

```text
1. snapshot strategy wallet own capital excluding unrealized P/L
2. include all realized P/L already reflected in wallet capital
3. set daily_portfolio_base for the new accounting day
4. preserve prior accounting-day record for exactly-once late final postings
5. reset daily_realized_pnl
6. reset Daily Loss Limit state
7. recalculate percentage-based portfolio limits
8. start new accounting day
```

`daily_portfolio_base` is fixed until the next rollover.

---

# 4. Daily portfolio base and live P&L state

Portfolio Rules separates:

```text
daily_portfolio_base
current_portfolio_equity
daily_realized_pnl
unrealized_pnl
total_pnl
```

## 4.1 Daily portfolio base

Canonical:

```text
daily_portfolio_base
=
strategy_wallet_capital_at_rollover_excluding_unrealized_pnl
```

The base is fixed for the whole accounting day.

Realized P&L accumulated during the previous day is already reflected in strategy wallet capital by the next rollover and therefore becomes part of the next day's `daily_portfolio_base`.

Example:

```text
Day 1 base = $1,000
realized P&L during Day 1 = +$80

next rollover:
new daily_portfolio_base = $1,080
```

Unrealized P&L from still-open exposure is **not** included in the new daily base until it becomes realized.

## 4.2 Live portfolio equity and P&L

Portfolio Rules must still track and expose current live portfolio state:

```text
current_portfolio_equity
daily_realized_pnl
unrealized_pnl
total_pnl
```

Canonical relationship for display/diagnostics:

```text
total_pnl
=
daily_realized_pnl
+
unrealized_pnl
```

`current_portfolio_equity` reflects the live account value including unrealized P&L.

Example:

```text
daily_portfolio_base = $1,080
daily_realized_pnl = +$20
unrealized_pnl = -$35

current portfolio equity ≈ $1,065
```

The exact account-equity field is an API fact; Portfolio Rules does not derive exchange equity by approximation when a canonical account value is available.

## 4.3 Intraday rule-base invariant

During the accounting day:

```text
daily_portfolio_base = constant
```

Therefore unrealized P&L:
- is visible;
- is stored;
- contributes to live equity / total P&L;
- does **not** continuously rebase percentage Portfolio Rules.

This prevents intraday limits from expanding or contracting every time floating P&L moves.

External deposits/withdrawals are capital flows, not trading P&L. They are recorded immediately in live portfolio state but do not change the current day's percentage denominator until the next rollover unless a future approved version explicitly changes that policy.

---

# 5. User Portfolio Rules configuration

Baseline user-configurable fields:

```yaml
portfolio_rules:
  max_capital_in_positions_pct:

  max_open_positions:

  max_positions_per_coin:

  minimum_tranche_capital:  # UI label: Minimum Position Capital

  daily_loss_limit:
    enabled:
    pct:

  cooldown_minutes:

  coins:
    - symbol:
      enabled:
      allocation_pct:
```

General Portfolio Rules settings are uniform across coins.

Only:
- symbol;
- enabled state;
- coin allocation

are coin-specific in baseline.

---

# 6. Derived global limits

## 6.1 Max capital in positions

```text
global_position_cap =
daily_portfolio_base
×
max_capital_in_positions_pct / 100
```

This cap is based on own committed capital.

It is not based on leveraged order notional.

---

# 7. Derived coin allocation

For each enabled coin:

```text
coin_allocation_cap[symbol]
=
daily_portfolio_base
×
coin_allocation_pct[symbol] / 100
```

Coin Allocation is simultaneously:

```text
TARGET
+
HARD CAP
```

TARGET:
Portfolio Rules continues seeking valid tranches while free coin capital remains.

HARD CAP:
Portfolio Rules must not intentionally exceed the coin allocation cap.

---

# 8. Coin allocation sum semantics

It is valid for:

```text
sum(all coin allocation caps)
>
global_position_cap
```

because the global cap is the runtime hard limit.

Example:

```text
global position cap = 60%

SOL = 20%
ETH = 20%
DOGE = 20%
BTC = 20%
```

Configuration is valid.

The portfolio cannot fill all 80% simultaneously because the 60% global cap always wins.

---

# Part II — Canonical Portfolio State Synchronization

## 9. Portfolio Rules-owned state

There is no separate `Portfolio State` architecture block.

Portfolio Rules owns its accounting state and synchronizes factual account/order/position data through:

```text
Portfolio Rules ↔ API
Portfolio Data Request
```

Canonical internal state includes at least:

```yaml
portfolio_state:
  health: LIVE | RECONCILING | STALE
  as_of:

  daily:
    daily_portfolio_base:
    daily_realized_pnl:

  global:
    held_committed_capital:
    reserved_committed_capital:
    filled_committed_capital:
    closing_retained_committed_capital:
    committed_tranches:

  coins:
    - symbol:
      held_committed_capital:
      reserved_committed_capital:
      filled_committed_capital:
      closing_retained_committed_capital:
      committed_tranches:
      cooldown_until:
```

This is an internal Portfolio Rules state model, not a fifth architectural component.

Authoritative Portfolio Rules accounting is the merge of:

```text
local internal accounting state
+
API-confirmed exchange/account facts
```

Specifically:

```text
unresolved SUBMISSION_HOLD
```

is local Portfolio Rules state and cannot be reconstructed from the exchange API before submission/acceptance.

Therefore API refresh must never erase or free an unresolved local hold merely because that hold is absent from API data.

Free-capital equations always include unresolved local holds until they transition to:
- RESERVED;
- REJECTED;
- SUBMISSION_FAILED;
- explicitly released after a failed hold/submission path.


## 10. Refresh triggers

The primary state-change loop is:

```text
Order Lifecycle
→ Order Event
→ Portfolio Rules state = RECONCILING
→ Portfolio Data Request
→ API
→ confirm expected lifecycle state
→ merge API-confirmed facts with unresolved local SUBMISSION_HOLD
→ Portfolio Rules state = LIVE
→ Portfolio Rules recomputes state
→ Portfolio Rules updates Coins OPEN / CLOSE
→ Portfolio Rules updates Capital and Limits
```

Relevant `Order Event` examples include:
- placed / accepted;
- rejected;
- submission failed;
- partial fill;
- full fill;
- cancellation;
- close.

Portfolio Rules also refreshes/reconciles state on:
- startup;
- reconnect/recovery;
- explicit reconciliation;
- other situations where state health is not confidently `LIVE`.

A Position Rules `APPROVE / REJECT` is also a Portfolio Rules decision event:
- `REJECT` creates no hold;
- `APPROVE` creates the correlation needed to attempt `SUBMISSION_HOLD`.

If the API refresh cannot confirm the expected lifecycle change:

```text
state remains RECONCILING or becomes STALE
```

and:

```text
no new exposure
no new Coin OPEN caused by that unresolved capacity
no new Capital and Limits based on uncertain freed capacity
```

Portfolio Rules must not reopen capacity from a single stale API read immediately after an `Order Event`.


## 11. State health

Portfolio Rules may issue new capital grants only when state is sufficiently synchronized.

Canonical health:

```text
LIVE
RECONCILING
STALE
```

If:

```text
health != LIVE
```

then new exposure is blocked:

```text
status = UNAVAILABLE
reason = PORTFOLIO_STATE_UNAVAILABLE
```

Existing exchange-side protective orders and already open positions are unaffected.

---

# 12. Normalized logical tranche states

Slot-consuming states are every unresolved SUBMISSION_HOLD and every nonterminal accepted tranche: RESERVED, PARTIALLY_FILLED, OPEN, CANCEL_PENDING, CLOSE_PENDING and RECONCILING (including manual-intervention escalation with unresolved commitment). Terminal CLOSED, CANCELLED_ZERO_FILL, definitive pre-create REJECTED/SUBMISSION_FAILED consume no slot only after their authoritative terminal predicates.

CLOSED has exactly the six predicates in P6, including financial finality and resolved execution authority. A zero physical quantity does not release capital or a slot. All free-capital projections include closing_retained_committed_capital.

---

# 13. Submission hold and reservation start

P1 governs the exact sequence:

```text
Set MATCHED → Market Handoff
Position → Portfolio: initial APPROVE / REJECT (no capital_grant_id)
REJECT → no grant/hold/spec
APPROVE → Portfolio issues immutable Capital and Limits with new capital_grant_id
Position → Lifecycle: final Order Spec after construction
Position → Portfolio: matching CONSTRUCTION_RESULT(CONSTRUCTED)
Portfolio atomically rechecks current gates/capacity and books exact-actual-commitment SUBMISSION_HOLD
Portfolio → Lifecycle: Submit Authorized
Lifecycle requires matching spec + authorization before hard technical validation/native submit
```

Initial APPROVE creates no hold. First complete constructed approval to book current capacity wins. A hold failure produces no authorization or native submission and does not resize the spec or rerun Set. Accepted native entry transitions hold to actual reservation under §44; definitive no-create failure releases it only with proof. Ambiguity retains it. Holds are durable local accounting, have no trading expiry and do not start cooldown.

---

# 14. Reservation accounting

P6 defines four mutually exclusive components. For a coin and globally:

```text
committed_coin_capital = held_coin_capital + filled_coin_committed_capital
                       + reserved_coin_capital + closing_retained_coin_capital
committed_global_capital = held_global_capital + filled_global_committed_capital
                         + reserved_global_capital + closing_retained_global_capital
logical_committed_capital[tranche] = held + reserved + filled + closing_retained
```

The formula names are sums of the corresponding *_committed_capital ledger fields. During ordinary entry, the existing hold/reserve/fill apportionment applies. At close acquisition the accepted commitment is transferred atomically into closing_retained_committed_capital, preserving its entire amount. This is not exposure, filled quantity or actual exchange margin. Closing entry cancellations/partial exits cannot reduce this locked total before canonical CLOSED.

---

# 15. Free capital

Every projection uses all four components:

```text
free_coin_capital = coin_allocation_cap - held_coin_capital
                  - filled_coin_committed_capital - reserved_coin_capital
                  - closing_retained_coin_capital
free_global_capital = global_position_cap - held_global_capital
                    - filled_global_committed_capital - reserved_global_capital
                    - closing_retained_global_capital
```

The same logical amount cannot appear in two components. A flat-but-nonterminal closing tranche retains its full own-capital commitment explicitly in closing_retained_committed_capital, not in a fake filled quantity. Diagnostic clamping never hides a true hard-cap breach.

---

# 16. Remaining tranche slots

Global:

```text
remaining_global_slots =
max_open_positions
-
global_committed_tranches
```

Per coin:

```text
remaining_coin_slots =
max_positions_per_coin
-
coin_committed_tranches
```

where committed tranches are:

```text
all unresolved holds and all nonterminal logical tranches, including CLOSE_PENDING / RECONCILING
```

---

# 17. Dynamic tranche sizing

Canonical:

```text
requested_capital_per_tranche
=
free_coin_capital
/
remaining_coin_slots
```

Preconditions:

```text
free_coin_capital > 0
remaining_coin_slots > 0
```

Example:

```text
SOL cap = $1,000
filled = $248.90
reserved = $0
remaining slots = 3

free coin capital = $751.10

requested capital per tranche
= 751.10 / 3
≈ $250.37
```

---

# 18. Minimum Tranche Capital

User rule:

```text
minimum_tranche_capital
```

Recommended UI label:

```text
Minimum Position Capital
```

Meaning:

```text
minimum amount of the user's own capital
for which Portfolio Rules is allowed to create one new logical tranche
```

Hard gate:

```text
requested_capital_per_tranche
>=
minimum_tranche_capital
```

If not:

```text
BLOCKED
reason = MINIMUM_TRANCHE_CAPITAL_NOT_MET
```

This rule intentionally prevents endlessly fragmenting residual coin allocation into tiny positions.

Example:

```text
SOL coin allocation = $1,000
Minimum Position Capital = $100
remaining free SOL capital = $50

$50 < $100
→ no new SOL tranche
→ residual $50 remains unused
```

Residual capital below the threshold remains free/unused.

Portfolio Rules does not:
- create a micro-tranche;
- merge the residual into another trade automatically;
- shrink the configured minimum;
- force exhaustion of the coin allocation.

The threshold applies to **own capital**, not leveraged order notional.

---

# 19. Global capacity gate

A tranche is allowed only if:

```text
free_global_capital
>=
requested_capital_per_tranche
```

If not:

```text
BLOCKED
reason = INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE
```

Do not shrink the current tranche arbitrarily to fit global capacity.

---

# 20. Max Open Positions gate

Require:

```text
global_committed_tranches
<
max_open_positions
```

Else:

```text
BLOCKED
reason = MAX_OPEN_POSITIONS_REACHED
```

---

# 21. Max Positions per Coin gate

Require:

```text
coin_committed_tranches
<
max_positions_per_coin
```

Else:

```text
BLOCKED
reason = MAX_COIN_POSITIONS_REACHED
```

---

# 22. Coin allocation gate

Require:

```text
free_coin_capital > 0
```

Else:

```text
BLOCKED
reason = COIN_ALLOCATION_REACHED
```

---

# 23. Daily Loss Limit

The original threshold remains:

```text
daily_loss_limit_amount = daily_portfolio_base × daily_loss_limit_pct / 100
daily_realized_pnl[accounting_day_id] = sum(FINAL logical net results bound to that accounting_day_id)
if enabled and current_day.daily_realized_pnl <= -daily_loss_limit_amount:
    latch DAILY_LOSS_LIMIT_REACHED for the current day
```

P8 binds each result to the day containing the proven permanent final closing execution (accounting_effective_at), not operational cleanup, financial finalization or delivery time. Lifecycle's final result is the sole logical authority; incomplete evidence produces no provisional posting. Required financial finality is part of canonical CLOSED, not an optional post-CLOSED step.

First receipt posts result_id exactly once to its immutable day; duplicate result or tranche final identity cannot post again. A late historical result fills only that historical day and never changes current-day Daily Loss/latch, current daily_portfolio_base, or adds P&L again to API-authoritative wallet capital. Portfolio stores delivered_at separately in its receipt ledger. Current-day latch resets only at next rollover.

The gate blocks new Coin OPEN and new grants/holds. It never force-closes positions, cancels existing entries/protection or creates a funding/time-based exit.

A-009 uses the following exact totals, diagnostic and ordered gate
branches. The diagnostic loss-used amount does not replace the signed predicate.

For accounting day `d`:

```text
R_d = sum(net_realized_result_i)
      for each eligible FINAL logical result i
      with accounting_day_id_i = d
      posted exactly once under result_id and tranche_id

L_d = daily_portfolio_base_d * daily_loss_limit_pct / 100

daily_loss_used_amount_d = max(-R_d, 0)
```

Gate rule:

```text
if daily_loss_limit_enabled is false:
    daily_loss_status = DISABLED
    daily_loss_blocks_new_exposure = false

else if current_day_latch is already set:
    daily_loss_status = LATCHED
    daily_loss_blocks_new_exposure = true

else if required day/base/configuration/recovery state is unavailable:
    daily_loss_status = UNAVAILABLE_OR_FAIL_CLOSED
    daily_loss_blocks_new_exposure = true

else if R_current_day <= -L_current_day:
    latch DAILY_LOSS_LIMIT_REACHED for the current accounting day
    daily_loss_status = LIMIT_REACHED or LATCHED
    daily_loss_blocks_new_exposure = true

else:
    daily_loss_status = OK
    daily_loss_blocks_new_exposure = false
```

Equivalent exact comparison:

```text
100 * R_current_day <= -(daily_portfolio_base_current_day * daily_loss_limit_pct)
```

The branches above are ordered: disabled first, then the retained current-day
latch, then unavailable required state, then the inclusive threshold comparison.
Disabling the gate does not erase its latch; re-enabling during that same
accounting day encounters the retained latch. A reconstructed total alone does
not recover latch history. Preserve the existing next-day rollover rule.

For an enabled evaluable comparison, require the existing ACCOUNTING_DAY_V1
boundary identity/instants, fixed governed daily base, valid positive configured
percentage and restored day/receipt/latch/base/commitment/critical-incident state.
No new base-reconstruction policy or percentage ceiling is introduced. Included
results are complete governed-currency FINAL A-002 logical results with valid
result/tranche/day identity, posted once under both identities. An actually
empty eligible result set with recovered receipt/day state sums to zero;
missing receipt or recovery evidence must not be represented as an empty set.
Conflicting result/tranche identity is an integrity conflict, not permission to
rewrite totals. Native aggregate P&L and unrealized P&L are not additional
summands or substitutes.

When disabled, the Daily Loss gate supplies no blocking and requires no
base/final-result evidence for that decision. This does not waive independent
receipt, recovery, accounting or other integrity gates. The existing
Asia/Jerusalem civil-midnight boundaries and economic closing execution day
remain authoritative; receipt/cleanup/finalization times cannot substitute.
Historical results remain on their immutable historical day and do not change
today's base/latch or re-credit API-authoritative wallet capital.

L_d is an exact comparison threshold, not a newly quantized cash posting.
Finite decimal products and division by 100 retain exact digits (or exact
rational representation); no cents/Qcapital/report rounding, binary float,
epsilon or arbitrary finite-precision context may change the comparison.
Keep R_current_day <= -L_current_day rather than loss_used >= L_current_day,
including if an upstream base policy admits zero base. This gate adds no
cancellation, exit or capital-release authority.

---

# 24. Cooldown

User rule:

```text
cooldown_minutes
```

For each symbol:

```text
cooldown_until[symbol]
```

For each authorized entry attempt, Portfolio pins the cooldown duration from the exact Portfolio Rules configuration selected in the atomic hold/authorization transaction before `Submit Authorized` is emitted. Persist with the attempt at least the Portfolio `configuration_id`, `configuration_version`, canonical `configuration_content_digest`, `pinned_cooldown_duration`, `authorization_id` and `tranche_id`. The attempt's cooldown begins only when authoritative `entry_accepted_at` is proven.

Canonical:

```text
cooldown_until
=
entry_accepted_at
+
pinned_cooldown_duration
```

A later Portfolio Rules edit, including a new `cooldown_minutes`, affects only future authorized attempts. If acceptance is recovered late or after restart, use the attempt's persisted pinned duration; never the then-current setting. Once `cooldown_until` exists it is not recalculated because configuration changed.

During:

```text
now < cooldown_until
```

new same-symbol cycle is blocked.

Reason:

```text
COIN_COOLDOWN_ACTIVE
```

---

# 25. Cooldown scope

Cooldown state is per symbol.

Example:

```text
SOL cooldown active
DOGE cooldown inactive
```

DOGE may proceed.

Baseline does not distinguish LONG vs SHORT cooldown.

A cooldown on SOL blocks a new SOL cycle regardless of direction because direction is not known until Set runs.

---

# 26. Cooldown expiry

At:

```text
now >= cooldown_until
```

Portfolio Rules reevaluates its current synchronized portfolio/accounting state.

If:
- free coin capital remains;
- free global capital remains;
- tranche slots remain;
- Daily Loss Limit permits;
- state is LIVE;

then the symbol may become `OPEN` again for Set analysis.

Old Set Results are never reused.

---

# 27. Pending LIMIT orders after cooldown

A pending LIMIT order may still exist when cooldown expires.

It continues to consume:

```text
reserved committed capital
+
one logical tranche slot
```

Portfolio Rules may issue another same-symbol cycle only from:

```text
remaining genuinely free capital
+
remaining genuinely free tranche slots
```

---

# 28. Partial fill accounting

Suppose:

```text
reserved capital = $250
```

Partial fill converts part of reservation to actual committed capital.

Example:

```text
actual committed capital from fill = $100
remaining reservation = $150
```

Total committed remains:

```text
$250
```

Conceptually:

```text
filled_committed_capital
+
reserved_committed_capital
=
total tranche committed capital
```

---

# 29. Full fill

On full fill:

```text
reserved capital → 0
actual committed capital → actual filled committed capital
```

The tranche remains slot-consuming as:

```text
OPEN
```

---

# 30. Zero-fill cancel/reject

If an accepted pending order later ends with no fill:

```text
reservation released
logical tranche slot released
```

State becomes:

```text
CANCELLED_ZERO_FILL
```

If rejected before exchange acceptance:

```text
no reservation is created
```

State becomes:

```text
REJECTED
```

---

# 31. Partial-fill cancel

Before any close intent, terminal cancellation of an entry remainder releases only its unfilled reservation; actual filled commitment and the tranche slot remain for open exposure. No top-up/re-entry is added.

Once a close intent has acquired the tranche, P6 freezes the entire current commitment in closing_retained_committed_capital. Cancellation of its remaining entry quantity during close reconciliation does not release part of that locked amount. It stays retained until canonical CLOSED, even if exposure becomes zero.

---

# 32. Position close effects

Allowed close events:

```text
TAKE_PROFIT
STOP_LOSS
MANUAL_CLOSE
```

Only on final `CLOSED` after all terminal predicates are satisfied:

```text
actual committed capital released
logical tranche slot released
```

Financial posting is separate in delivery timing, not optional finality: `daily_realized_pnl` updates only when Lifecycle delivers the authoritative financially complete logical result. No partial exit execution releases committed capital or a slot, and no provisional P/L is posted.

Closing does not itself create a new cooldown.

Cooldown is entry-order based.

---

# Part III — Coins OPEN / CLOSE

## 33. Analysis need belongs to Portfolio Rules

Portfolio Rules, not Set, decides whether each symbol should currently be analyzed for a new opportunity.

Canonical interface:

```text
Portfolio Rules → Set
Coins
```

Each symbol carries:

```text
OPEN
CLOSE
```

Semantics:

```text
OPEN
= Set should start / continue new-opportunity analysis for this symbol

CLOSE
= Set should stop new-opportunity analysis for this symbol
```

`CLOSE` concerns only **new opportunity search**.

It does not terminate Set monitoring for an already placed pending order associated with an existing `decision_cycle_id`.

## 34. When a coin is OPEN

A symbol may be `OPEN` only when all relevant Portfolio Rules gates permit new exposure:

```text
configuration valid
state LIVE
symbol enabled
Daily Loss Limit permits
cooldown expired
global tranche slot available
coin tranche slot available
free coin capital > 0
requested_capital_per_tranche >= minimum_tranche_capital
free global capital >= requested_capital_per_tranche
```

If all pass:

```text
Coin status = OPEN
```

If any blocking gate fails:

```text
Coin status = CLOSE
```

`OPEN` remains active across repeated Set evaluations.

Therefore:

```text
Set evaluates → NONE
```

does not require Portfolio Rules to send a new request.

The symbol simply remains:

```text
OPEN
```

until Portfolio Rules changes it to `CLOSE`.

## 35. OPEN / CLOSE reevaluation triggers

Portfolio Rules reevaluates coin status when its own state may have changed, including:

```text
Order Event processed
APPROVE / REJECT processed
cooldown expiry
daily rollover
user Portfolio Rules configuration change
startup / reconciliation completion
manual portfolio-affecting action
```

Portfolio Rules does not define Set timeframes, candles, trigger cadence, or market-analysis timing.

Those are Set-internal methodology.

## 36. Idempotency and ordering

Portfolio Rules may emit `OPEN / CLOSE` only when status changes or resend the current status idempotently, but every symbol delta carries a Portfolio-owned monotonically increasing `scope_revision`.

Canonical payload fragment:

```yaml
symbols:
  - symbol:
    scope_revision:
    action: OPEN | CLOSE
```

Set applies only a revision newer than the last applied revision for that symbol. Arrival time is not authoritative; an older delayed OPEN can never overwrite a newer CLOSE. Omitted symbols are unchanged because this contract is delta-based.

---

# Part IV — Capital and Limits

## 37. Purpose

Portfolio issues Capital and Limits only after receiving and persisting initial Position APPROVE for the Set-created cycle. REJECT does not issue a grant. The grant is an immutable factual/capital snapshot for that exact decision/cycle and consumes no capacity. P1–P2 govern creation, delayed delivery and current hard compatibility.

## 38. Canonical Capital and Limits payload

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

capital_grant_id is created in Portfolio's post-APPROVE issue transaction with provenance and outbox. The grant contains the existing decision_cycle_id, set_result_id and position_decision_id; the initial APPROVE has none of the grant/final-plan IDs. Duplicate APPROVE reuses the same grant. No symbol matching or replacement grant is used for replay.

## 39. Factual revisions and later grants

Later independent approved opportunities receive snapshots of current Portfolio state. A newer revision does not mutate or expire an existing grant. Only exact-spec incompatibility with a current hard venue constraint blocks native execution; no TTL, fee-driven re-evaluation, quantity resize or Entry/TP/SL/leverage repair is introduced. Current Portfolio gates/capacity are separately rechecked at atomic hold. Native hard compatibility is Lifecycle-owned through Order Management, never a Position API call.

---

# Part V — Approve / Reject and decision-cycle correlation

## 40. REJECT

Initial OPPORTUNITY_DECISION(REJECT) ends the opportunity, with no grant, hold, final plan/tranche/spec or authorization. Its exact Set cycle and Position decision identity remain audit records. An eligible symbol may continue searching for a fresh independent opportunity.

## 41. Initial APPROVE and post-grant construction

Initial APPROVE carries only the exact opportunity decision, with no capital_grant_id. It permits Portfolio to create and issue the one immutable Capital and Limits. It does not book capital.

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

Only after the grant, successful final construction confirms the exact spec/capital over this same return boundary:

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

A construction REJECT is consumed without hold/spec and retains actual failed-gate diagnostics. Initial APPROVE is not repeated. Position's confirmation and spec share all final IDs/digest; Portfolio never reconstructs them from symbol. Enabled Minimum Net Edge must be PASS, disabled NOT_APPLICABLE for successful construction.

### 41.1 Atomic hold transaction

In one durable transaction, first select and pin the exact current Portfolio Rules configuration binding for this prospective authorized attempt, including its `pinned_cooldown_duration`; then verify LIVE/coherent Portfolio state, current Daily Loss latch, symbol policy/scope, cooldown, current coin/global capacity and slots; verify grant existence, approved cycle/decision binding and nonconsumption; verify immutable construction plan/tranche/spec/economics/digest and no conflicting binding. Then require actual_committed_capital <= requested_capital_per_tranche and book the exact canonical actual_committed_capital as SUBMISSION_HOLD, consume the grant once, create authorization_id and persist its outbox. A duplicate identical construction is a no-op. A conflicting binding is an integrity failure. First bookable constructed approval wins; failure emits no authorization and cannot repair the trade.

## 42. Hold accounting

Hold consumes own capital and one slot immediately. It survives delayed/missing spec and cannot be erased by an API query that finds no order. Native acceptance reclassifies the same exact approved actual capital; unused grant capacity was never held. No trading expiry exists.

## 42A. Submit Authorized / Order Submit

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

State/authorization publication are atomic and replay retains the same ID. Lifecycle requires the matching exact spec/digest; either input may arrive first. No hold means no authorization; no matching pair means no exchange side effect.

---

# Part VI — Order Event feedback

## 43. Order Event

Order Lifecycle sends:

```text
Order Lifecycle → Portfolio Rules
Order Event
```

`Order Event` is the canonical trigger that an exchange/order lifecycle fact may have changed.

Portfolio Rules does not trust the event as a complete account snapshot.

Instead:

```text
Order Event
→ Portfolio Rules state = RECONCILING
→ Portfolio Data Request
→ API
→ authoritative refresh / reconciliation
→ merge API-confirmed facts with unresolved local SUBMISSION_HOLD
→ Portfolio Rules state = LIVE
→ recompute Portfolio Rules state
```


## Approved capital-per-unit apportionment

Canonical baseline:

```text
approved_capital_per_unit
= approved_actual_committed_capital / approved_quantity

filled_committed_capital
= approved_capital_per_unit × cumulative_filled_quantity  (pre-close only)

remaining_reserved_capital
= approved_capital_per_unit × remaining_entry_quantity
```

This is a logical Portfolio allocation basis, not exchange margin. Entry/exit price variation does not mutate the approved allocation basis. Any deterministic decimal residue caused by quantity/currency precision is retained on the remaining component while a remainder exists and, at final terminalization, is assigned to the filled/closed tranche so that total logical allocation exactly conserves the approved actual committed capital.

Atomic transition rule:

```text
remove prior hold/reserved component
+ add new filled/reserved components
= one logical update
```

The same capital amount may never simultaneously exist as full hold and full reserve/fill.

Before close acquisition these are entry-allocation components. At close acquisition P6 transfers their full sum to closing_retained_committed_capital using the fixed close_commitment_quantity_basis. Subsequent exit quantities do not reduce that retained sum. Closing-state events arriving ahead of acceptance are reconciled with the same immutable spec/hold before a single atomic allocation update.

## 44. Accepted / placed order

The grant is solely a construction bound. Before SUBMISSION_HOLD, Portfolio verifies the canonical actual commitment against the grant and against all current atomic capacity/slot/gate rules. An excess over the grant fails without holding, authorization or resizing.

```text
held_amount = Order_Spec.economics.actual_committed_capital
held_amount = construction_result.approved_economics.approved_actual_committed_capital
held_amount = Submit_Authorized.held_committed_capital
held_amount <= requested_capital_per_tranche
```

For grant `100` and actual `90.666666666667`, hold is exactly `90.666666666667`; unused grant capacity `9.333333333333` remains free immediately. There is no acceptance-triggered grant-surplus release.

Native acceptance atomically removes SUBMISSION_HOLD and reclassifies the identical amount as RESERVED (or the existing cumulative filled/reserved components if fills arrived first). This is one allocation update, not an additional commitment. The one logical slot remains occupied. Actual/spec/confirmation/authorization inequality is an integrity failure; do not silently increase, shrink or repair any immutable trade.

Cooldown uses only original factual `entry_accepted_at` plus the already-persisted `pinned_cooldown_duration` for that authorization/tranche attempt. Missing acceptance evidence or `entry_acceptance_integrity.state = CONFLICT` keeps affected eligibility unresolved even if the first timestamp is known. Later fills do not extend cooldown. Acceptance receipt time is not its start. Current Portfolio configuration is never consulted to recompute an existing attempt.

---

## 45. Rejected / submission failed

Only for authoritative zero-execution rejection or definitive no-create failure with no in-flight/ambiguous request and all entry authority terminal (P2):

```text
SUBMISSION_HOLD released
slot released
no cooldown
```

## 46. Partial fill

The following apportionment applies before close acquisition. During an active close, P6 keeps the frozen closing-retained allocation unchanged despite entry/exit fills. A partial fill is a real logical tranche.

Accounting:

```text
exact filled basis = approved_capital_per_unit × cumulative_filled_quantity
exact remainder basis = approved_capital_per_unit × remaining_entry_quantity
persisted filled/reserved values = TT_NUMERIC_V1 §5 apportionment
(all residue retained; do not independently round these two products)
```

The slot remains occupied.

## 47. Full fill

Before close acquisition, on full fill:

```text
remaining reservation → 0
actual committed capital → actual filled committed capital
logical tranche → OPEN
```

## 48. Zero-fill cancellation

Outside the active close path, if an accepted pending entry is authoritatively cancelled with zero fill, all associated execution authority is terminal and reconciliation proves no execution:

```text
reservation released
slot released
```

For the baseline product semantics:

```text
cooldown for that cancelled zero-fill attempt is cleared
```

Portfolio Rules then reevaluates the symbol.

## 49. Partial-fill cancellation

Before a close intent, release only the authoritatively terminal unfilled entry reservation, retaining the filled portion and slot. During an active close, P6 retains the entire frozen closing commitment instead. No old-tranche automatic top-up occurs.

---

## 50. Position close

A TP, SL, or Manual Close **intent** does not itself release capital. Partial execution of any such exit remains an intermediate close state. Portfolio releases own committed capital and the tranche slot only when Order Lifecycle emits final `CLOSED` after every terminal predicate is authoritative.

Daily Loss is posted from the authoritative FINAL result included in canonical CLOSED publication, after all mandatory evidence is COMPLETE. Delivery may be later; P8 preserves its original economic accounting day.

Closing does not itself create a new cooldown.

---

# Part VII — Portfolio Rules outputs and diagnostics

## 51. Canonical decision/status model

Portfolio Rules uses:

```text
ALLOWED
BLOCKED
UNAVAILABLE
```

for its internal gating decisions.

`Coins OPEN / CLOSE` is the external analysis-scope output.

`Capital and Limits` is the external capital-context output.

`SUBMISSION_HOLD` is the post-grant CONSTRUCTED-confirmation accounting action; initial opportunity APPROVE cannot book it.

## 52. Gate result

```yaml
gate_result:
  gate_id:
  status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
  configured_value:
  calculated_value:
  operator:
  reason_code:
  dependency_reason:
```

## 53. Core reason codes

```text
INVALID_PORTFOLIO_CONFIGURATION
PORTFOLIO_STATE_UNAVAILABLE
SYMBOL_DISABLED
DAILY_LOSS_LIMIT_REACHED
MAX_OPEN_POSITIONS_REACHED
MAX_COIN_POSITIONS_REACHED
COIN_ALLOCATION_REACHED
COIN_COOLDOWN_ACTIVE
MINIMUM_TRANCHE_CAPITAL_NOT_MET
INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE
NO_REMAINING_COIN_CAPITAL
NO_REMAINING_COIN_SLOTS
CONCURRENT_CAPACITY_CONFLICT
```

All evaluated reasons should be persisted even when one primary reason is selected.

# 54. Daily rollover event contract

Canonical internal event:

```yaml
daily_rollover:
  timezone: Israel
  rollover_at:

  previous_daily_portfolio_base:
  previous_daily_realized_pnl:

  new_daily_portfolio_base:
  base_source: STRATEGY_WALLET_CAPITAL_EX_UNREALIZED
  new_daily_realized_pnl: 0
```

After rollover, all percentage-based portfolio limits are recalculated.

---

# 54A. No-repair invariant

Portfolio Rules may not repair a blocked trade by:

```text
changing Set direction
changing Position Rules leverage
changing Entry / SL / TP
shrinking tranche arbitrarily
ignoring reserved capital
ignoring cooldown
ignoring Daily Loss Limit
using leveraged notional as portfolio capital
```

It may only:
- calculate;
- gate;
- request;
- reserve through the lifecycle transition;
- block;
- wait for state change.

---

# 55. Portfolio Rules and leverage

Leverage belongs entirely to Position Rules.

Portfolio Rules sees:

```text
requested_capital_per_tranche
actual_committed_capital
```

It may persist:

```text
target_order_notional
actual_order_notional
```

for history/diagnostics, but these do not affect allocation management.

---

# 56. Portfolio Rules and funding

Funding is not part of portfolio eligibility or allocation sizing in baseline methodology.

If funding is realized later, it contributes to realized P/L through the trade lifecycle and therefore eventually affects:

```text
daily_realized_pnl
```

when recognized in realized trade economics.

Portfolio Rules does not predict future funding.

---

# Part VIII — Canonical boundaries

## 59. Set boundary

Portfolio Rules decides:

```text
which symbols are OPEN / CLOSE
```

It does not decide:
- LONG / SHORT / NONE;
- market regime;
- market structure;
- market invalidation.

Set owns those.

## 60. Position Rules boundary

Portfolio Rules owns:

```text
requested_capital_per_tranche
Capital and Limits
SUBMISSION_HOLD
```

Position Rules owns:
- Entry;
- SL;
- TP;
- leverage;
- quantity;
- economics;
- APPROVE / REJECT;
- Order Spec.

Portfolio Rules must not change trade geometry to make a trade fit.

## 61. Order Lifecycle boundary

Portfolio Rules does not own:
- submission;
- exchange acknowledgement;
- fill mechanics;
- cancellation mechanics;
- retry/reconciliation mechanics;
- close execution.

It receives `Order Event`, refreshes factual state through API, and updates its accounting.

## 62. Pending-order market validity boundary

Portfolio Rules does not decide whether a pending LIMIT remains market-valid.

That responsibility belongs to Set.

If Set sends `Order Cancel Signal`, Order Lifecycle executes cancellation.

Portfolio Rules reacts only to the resulting lifecycle/account state through `Order Event` + API refresh.

---

# 63. Research and diagnostics

Persist at least:

```text
Coins OPEN / CLOSE transitions
Capital and Limits grants / blocks
gate failure frequencies
cooldown block frequency
daily loss block frequency
global cap block frequency
coin cap block frequency
slot utilization
capital utilization
coin allocation utilization
submission hold duration
reserved capital duration
requested tranche capital
actual committed capital
target order notional
actual order notional
reconciliation count / frequency
concurrency conflicts
missed opportunities due to capacity

capital grant created_at
capital grant amount
capital grant consumed_at / closed_at
hold created_at
hold amount
actual reserved capital
released rounding delta
reconciliation started_at
reconciliation completed_at
reconciliation failure reason

```

---

# Part IX — Canonical Portfolio Rules Invariants

1. Portfolio Rules manages **own committed capital**, never leveraged notional.
2. Daily accounting boundary is `00:00 Israel local time`.
3. `daily_portfolio_base` excludes unrealized P/L and remains fixed intraday.
4. Coin Allocation is both target and hard cap.
5. Global Max Capital in Positions always wins over aggregate coin targets.
6. Pending accepted LIMIT orders consume capital and tranche slots.
7. `SUBMISSION_HOLD` consumes capital and one slot before submit eligibility; successful hold emits `Submit Authorized`.
8. Cooldown starts only after successful exchange acceptance of the LIMIT entry.
9. Cooldown is per symbol.
10. Daily Loss Limit blocks only new exposure; it does not force-close existing exposure.
11. Portfolio Rules owns `Coins OPEN / CLOSE`.
12. Set remains responsible for all market-analysis timing and logic.
13. `Set = NONE` does not require any Portfolio Rules action; an eligible coin simply remains `OPEN`.
14. Portfolio Rules does not create `decision_cycle_id`.
15. Initial APPROVE supplies the Set cycle; only then can Portfolio issue its bound grant. Hold follows post-grant construction.
16. On `REJECT`, no hold is created.
17. Every later independent grant reflects current held/reserved/filled/closing-retained commitment.
18. `Order Event` triggers API-backed Portfolio Rules state refresh.
19. Portfolio Rules does not rely on a separate Portfolio State architecture block.
20. Partial fills separate filled committed capital from remaining reservation.
21. Zero-fill cancellation releases reservation and slot and clears that attempt's cooldown.
22. Pre-close entry cancellation releases only its unfilled reservation; close-path retention remains locked until CLOSED.
23. Old Set Results are never reused for a new trade.
24. First successfully bookable constructed approval wins when completed constructions compete for capacity.
25. Missing/stale factual state fails closed for new exposure.

26. Every `Capital and Limits` grant has an immutable Portfolio-owned `capital_grant_id`.
27. `Capital and Limits` is not a reservation and does not consume capacity by itself.
28. Initial APPROVE/REJECT has no grant; the post-grant construction result preserves the received capital_grant_id.
29. `SUBMISSION_HOLD` is keyed by `capital_grant_id + decision_cycle_id`.
30. API refresh never erases unresolved local `SUBMISSION_HOLD`.
31. After `Order Event`, Portfolio Rules becomes `RECONCILING` until expected lifecycle state is confirmed.
32. HOLD-to-RESERVED transfers the exact constructed actual committed capital without changing its amount; unused grant capacity was never held.
33. Positive rounding delta is released; over-grant actual capital is an integrity failure.
34. Unrealized P&L is always visible in live portfolio state but does not intraday-rebase `daily_portfolio_base`.
35. Next-day base uses the authoritative boundary wallet reconstruction; a result's later delivery never rebases it or adds the same wallet cashflow again (P8).
36. Residual coin capital below Minimum Position Capital remains intentionally unused.


---

# Appendix A — Attempt-scoped cooldown and ordered Coins projection (v1.1.0)

## Attempt-scoped cooldown

Each authorized attempt persists its Portfolio Rules configuration identity/version/content digest and `pinned_cooldown_duration` in the hold/authorization transaction. Once authoritative acceptance is proven, that tranche creates its own cooldown contribution:

```text
cooldown_contribution[authorization_id, tranche_id]
= entry_accepted_at + pinned_cooldown_duration
```

The effective symbol cooldown is:

```text
max(all surviving cooldown contributions for that symbol)
```

A confirmed zero-fill cancellation removes only that attempt's contribution. An older cancellation or replay can never shorten a newer accepted attempt's cooldown. Partial/full fill does not reset or extend the acceptance-derived contribution.

## Ordered Coins projection

Every emitted symbol OPEN/CLOSE delta includes `scope_revision`, monotonically increasing per symbol. Set must ignore older revisions. Omitted symbols are unchanged.

# Appendix B — Daily rollover recovery and metric scopes (v1.1.0)

Portfolio uses named timezone `Asia/Jerusalem` for the accounting boundary. Each day has an immutable `accounting_day_id` and half-open interval:

```text
[local 00:00, next local 00:00)
```

At rollover, the new fixed `daily_portfolio_base` is established from a verified wallet-own-capital snapshot at the resolved boundary instant excluding unrealized P&L, or from deterministic reconstruction using complete authoritative cashflow history that spans the boundary.

If the boundary value cannot yet be proven:

```text
rollover_state = RECONCILING
new exposure = blocked
previous established base remains immutable for historical reporting
```

A later arbitrary snapshot is never substituted as if it were the missing boundary snapshot, and no intraday rebase occurs.

Metric scopes are distinct:

```text
daily_realized_pnl
= existing Daily Loss metric: FINAL lifetime net results whose immutable accounting_day_id equals this day (P8)

current_portfolio_equity
= authoritative current account equity from API

unrealized_pnl
= authoritative current floating account P&L

cash_period_pnl
= optional separately labeled cashflow metric for the declared period; never substituted for daily_realized_pnl
```

`daily_portfolio_base + daily_realized_pnl + unrealized_pnl` is not defined as an equity identity. Realized cash already incorporated in wallet capital is never added again to the next day's base.

# Appendix C — Terminal slot release

Use all six P6 CLOSED predicates, including fully resolved intent, financial finality and no competing execution authority. Until then retain the entire closing_retained_committed_capital and one slot, regardless of physical exposure. All free-capital formulas subtract the retained bucket. Zero exposure never implies zero logical commitment. Final release is once-only and replay-safe.

---

# Appendix D — Durable decision/authorization publication

State mutation and message publication on business-critical edges use a transactional outbox/inbox or an equivalent durability guarantee. In particular:

```text
successful SUBMISSION_HOLD + Submit Authorized publication
initial APPROVE persistence/publication; later grant issue; later CONSTRUCTED + immutable spec publication
material lifecycle state + Order Event / Set synchronization publication
```

must survive crash/restart with the same immutable IDs.

An authorization without a delivered spec remains backed by its local hold and is replayed/reconciled; a spec without authorization is a non-executing proposal. Neither condition creates an exchange failure, authorization timeout, or trading TTL. Absence of an exchange order alone never releases an unresolved local hold.

# Appendix E — Exit capital finality and unresolved native exposure

P6 governs full closing commitment/slot retention with no strategic partial-close or intermediate release. Portfolio distinguishes physical exposure from its retained logical commitment. Every TP/SL/Manual/external close path uses the same complete CLOSED predicate.

P9 governs native observation tombstones and independent native_scope_revision. Initial native observations block affected exposure without fabricated IDs. Strict logical allocation events alone cannot clear that block; a complete resolution manifest and all expected allocations applied once are mandatory. Resolved tombstones survive restart and reject regression by old replay. A different unresolved observation remains blocking.

# Appendix F — Final financial results, accounting days and receipts

P7–P8 are mandatory. Lifecycle retrieves actual financial facts through its own API boundary and publishes one FINAL result with COMPLETE evidence. Portfolio accepts once by both result_id and tranche_id, validates accounting_effective_at/accounting_day_id/policy and stores delivered_at. The result, current/historical accounting-day posting and terminal release are applied atomically. Old-day deliveries do not alter current Daily Loss/base or add cash to wallet again. API native aggregate P&L cannot substitute for the logical result. Restart restores receipts, day records, latch/base, commitment buckets and unresolved native observations before processing events.

---

# Appendix G — Numeric, cooldown and batch-fact synchronization

P11 and `schemas/NUMERIC_POLICY.md` apply to all capital formulas in this methodology: exact internal arithmetic; floor spendable capacity and per-slot grants at Qcapital; conservative actual commitment; exact final atomic limits; deterministic pre-close fill/reserve residue. A division expression in earlier sections is its exact mathematical basis, not permission to choose an arbitrary decimal context. Grants remain non-reserving; current atomic holds, four mutually exclusive commitment buckets and P6 close retention remain unchanged.

P10 is the complete cooldown merge rule: only proven original entry_accepted_at creates a deadline; a surviving accepted attempt with unknown time blocks new same-symbol eligibility. Cumulative Order Event version 7 carries the timestamp/status/provenance. Merge an older immutable fact without rolling back newer cumulative quantity/state, never extend it on a fill, and preserve cancellation tombstones. No local time or current updated_at fallback.

P14 specifies symbol-list Portfolio facts. Each requested instrument_metadata/fee_rates item independently identifies symbol/status/facts/as_of/source. Validate complete requested-set cardinality before using the batch; partial/unavailable mandatory facts keep the existing safe Portfolio state. The same normalized orders/executions can be read for factual reconciliation, but Portfolio does not reconstruct a competing logical financial result.

Construction confirmation version 5 binds exact duplicated canonical scalars to immutable Order Spec version 5; Portfolio's single atomic hold produces authorization version 5 for that exact target. P14 requires the independent producer scalar comparison; implementation conformance checks verify that comparison. Final result version 3 includes already committed P12 split evidence; Portfolio only consumes the authoritative logical result once and never reapportions native fees.

## Integrity and proof consumers

Apply SYSTEM_PROTOCOLS P10/P15 cumulatively: a known `entry_accepted_at` does not resolve `entry_acceptance_integrity.state = CONFLICT`. Persist per-attempt integrity revision/evidence/tombstone and keep affected eligibility blocked until an explicit authoritative resolution. A later PROVEN timestamp, stale Lifecycle revision or apparently expired cooldown cannot erase this conflict. Zero-fill cooldown removal is not integrity resolution.

Native-scope no-reduction Order Events contain no inferred logical ownership. Persist them and their partial/complete clearance manifests on the existing Lifecycle boundary. Block only their factual affected account/symbol/native side/index scope; do not apply a reduction, fee or capital change. Complete authoritative clearance plus the complete binding set (or proven terminal child/no authority) clears this observation; older observations cannot regress the tombstone. Other unresolved observations retain their blocks.

Capital/slot release is permitted only from a valid immutable CLOSED result whose Lifecycle publication established the current revision-bound predicate conjunction in P6/P13. API flatness or a cached chronology result is insufficient. Once-only result/day/receipt semantics remain unchanged; contradictory post-final evidence is an integrity condition, not a silent historical posting rewrite.

## Focused integrity/receipt synchronization

The active incoming Order Event version 7 and outgoing authorization version 5 retain their wire shapes. Apply P15/S03 content-consistency checks before resolved native-observation tombstones suppress replay. Same accepted observation revision with different canonical content creates durable affected-scope integrity blocking without logical ID fabrication, quantity effects or cashflow effects. Resolution-first history must retain what was actually proven/received; unknown observation content is not invented.

Lifecycle remains the financial owner. Portfolio consumes its committed terminal result and its integrity state on the existing edge. A known unresolved integrity incident blocks a not-yet-applied release; an already applied result/slot/capital receipt is never normally duplicated or silently reversed by contradictory later execution evidence. No new execution authorization is allowed from affected blocked eligibility. Canonical closing-retained commitment, exact constructed submission hold, current-gate concurrency and economic accounting-day attribution are unchanged.


## T01/T02 — Post-final incident inbox and receipt fence

Consume ORDER_EVENT v7 POST_FINAL_INTEGRITY independently of terminal-result and
lifecycle-revision dedupe. Persist incident revision/content history and the
affected native eligibility scope block. Same-revision contradictions block
even after resolution; no shared read of Lifecycle's local quarantine state is
allowed. Use the exact receipt/final-gate committed-prefix fence in
SYSTEM_PROTOCOLS T01: if an incident append committed first, an undelivered
message prevents first release. If the economic receipt committed first, retain
its immutable result/day and once-only capital/slot effect; block future scope
eligibility, never undo/re-add/re-release. Portfolio's receipt ledger, not the
producer's advisory receipt observation, is authoritative. Result identity is
unique by result_id and tranche_id; incident identity has its independent key.

T02 financial contradictions use the same inbox/fence. T04 native allocations
received before complete membership/source proof are staged without quantity
effect. A source partition and once-only application receipt, not allocation_id
alone, permit a reduction. Quantity reconciliation may complete while a separate
alias incident keeps scope eligibility blocked. No grant, hold, limit, Daily
Loss, historical-day posting or cooldown formula is changed.

## U02–U04 consumer clarification

Apply SYSTEM_PROTOCOLS.md U02–U04 on existing Order Event/entry-result boundaries. Keep the T01 committed-prefix receipt fence and independent incident/result dedupe. A changed accepted acceptance-resolution revision restores eligibility blocking while preserving the original factual acceptance timestamp; it does not start another cooldown. Confirmed filled exposure keeps its logical position slot and committed capital despite a contradictory rejection. Ordinary rejection release requires proven zero execution, no outstanding authority and bound entry terminality; a proofless status cannot supply those facts. Later factual exposure contradicting an earlier rejection is a reconciled liability, not another grant or authorization. Existing current capital/slot gates and limits are unchanged.


## V02/V03 producer-evidence consistency

SYSTEM_PROTOCOLS.md V02/V03 refine existing evidence ingestion, not Portfolio formulas or limits. A parent-linked post-final proof incident uses ORDER_EVENT v7 and the existing committed-prefix receipt fence. A pending receipt cannot release capital/slot while a known incident is pending or unresolved; an already applied receipt remains once-only and future eligibility is blocked. Revisionless acceptance contradictions published through the existing integrity fields leave the original accepted time immutable and make cooldown unresolved; they do not establish a new origin. No grant reservation, hold calculation, accounting-day policy or native-rejection predicate changes.
