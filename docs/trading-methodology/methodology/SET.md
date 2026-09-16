# TriggerTrade — Set Methodology

**File:** `SET.md`  
**Version:** 1.2.15
**Architecture role:** `Set — Market Analysis`


**Shared normative protocols:** `../SYSTEM_PROTOCOLS.md` (P1–P17). **ID ownership:** `../IDENTIFIER_LINEAGE.md`. Generated wire-shape illustrations use the strict schema registry in `../schemas/`; nullable annotations are not literal payload objects.

## Purpose

This is the single canonical methodology document for the TriggerTrade **Set** block.

It consolidates the previously reviewed/approved Set-related methodology into one domain document:

- Set formation and Trigger composition;
- market direction `LONG / SHORT / NONE`;
- approved Direction Classifier calculations;
- Market Handoff construction;
- creation of `decision_cycle_id`;
- frozen Market Invalidation Inputs;
- pending-order market-validity monitoring;
- Set runtime state and auditability.

No Set-owned methodology should live as a separate top-level architecture document after this document is approved.

The canonical external flows are:

```text
Portfolio Rules → Set
Coins: OPEN / CLOSE

Set → Position Rules
Market Handoff

Order Lifecycle → Set
Order Placed

Set → Order Lifecycle
Order Cancel Signal

Set ↔ API
Market Data Request
```

Set owns **market analysis only**.

Set does not own capital management, final trade construction, or order management.

---

# Part I — Canonical Set Architecture

## 1. Purpose

This document defines the canonical TriggerTrade **Set Contract**.

A Set is the market-analysis component of TriggerTrade.

It has two runtime responsibilities:

```text
1. INITIAL_ANALYSIS
2. PENDING_ORDER_MONITORING
```

In `INITIAL_ANALYSIS`, Set answers:

> Has the required market configuration formed for the requested coin, and what market direction does that configuration imply?

In `PENDING_ORDER_MONITORING`, Set answers:

> Does the still-pending LIMIT order created from this Set result remain valid under the frozen market-invalidation conditions of that original market setup?

Set does not define portfolio need.

Set does not define concrete position capital, leverage, final Entry, final Take Profit, final Stop Loss, order submission, or exchange-order management.

The canonical runtime flows are:

```text
Portfolio Rules
    ↓ Coins
Set — INITIAL_ANALYSIS
    ↓ Market Handoff
Position Rules
```

and, after an approved order is actually placed:

```text
Order Lifecycle
    ↓ Order Placed
Set — PENDING_ORDER_MONITORING
    ↓ Order Cancel Signal: INVALIDATION or MONITORING_UNAVAILABLE (§4.2)
Order Lifecycle
```

Set obtains current market data through its direct market-data API flow:

```text
Set ↔ API
Market Data Request
```

There is no KEEP signal. While the pending order remains valid and no previously established sticky cancellation requirement remains outstanding, Set emits no lifecycle-control message. Recovery does not withdraw such a requirement; see Part IV §12A.

---

## 2. Set inputs

Set has two canonical input types.

### 2.1 Coin analysis scope from Portfolio Rules

Portfolio Rules owns the decision about **which coins Set should currently analyze for new opportunities**.

The canonical flow remains:

```text
Portfolio Rules → Set
Coins
```

Each coin instruction carries one of two statuses:

```text
OPEN
CLOSE
```

Semantics:

```text
Coin OPEN
= start / keep this symbol active for new-opportunity analysis

Coin CLOSE
= stop new-opportunity analysis for this symbol
```

Portfolio Rules is therefore the sole owner of opening and closing the **analysis need**.

Set must not independently decide that a symbol should be added to or removed from the active analysis scope.

Examples:

```text
SOL OPEN
DOGE OPEN
BTC CLOSE
```

Set maintains the current active coin-analysis scope from these instructions.

Important boundary:

```text
Coin CLOSE
```

stops only **new-opportunity analysis** for that symbol.

It does **not** automatically terminate monitoring of an already placed pending order that has its own active `decision_cycle_id` and frozen Market Invalidation Inputs.

That pending-order monitoring continues until its own lifecycle termination condition is received or resolved.

Portfolio Rules does not send:
- tranche capital through `Coins`;
- leverage;
- trade economics;
- market direction;
- market-analysis timing rules;
- timeframe instructions.

Those remain outside the `Coins` scope contract.

---


### 2.1A OPEN scope revision as formation epoch

For unfinished formation, each effective `Coins OPEN` `scope_revision` establishes a fresh **formation epoch** for that symbol. Set persists the epoch as the exact OPEN `scope_revision` together with the pinned Set/Trigger/Core Set configuration binding required by P17. Every ARMED/PARTIALLY_MATCHED occurrence, retained pre-MATCH trigger event, sequence step, freshness state, temporal-window anchor and re-arm progress belongs to exactly one formation epoch.

An effective newer `CLOSE` terminates and resets every unfinished formation from the previous OPEN epoch. A later effective newer `OPEN` starts a new epoch with no carry-over of pre-CLOSE partial state. A newer OPEN also supersedes unfinished state from any older OPEN epoch even if an intermediate CLOSE delivery is delayed or never observed locally. Because Set applies `scope_revision` monotonically, `OPEN rev12` received before delayed `CLOSE rev11` establishes epoch 12 and invalidates an unfinished rev10 formation; the later rev11 CLOSE is stale and cannot undo rev12 or revive rev10.

Example:

```text
10:00 OPEN rev10; A fires -> PARTIALLY_MATCHED in epoch 10
10:01 CLOSE rev11 -> epoch-10 unfinished formation terminated/reset
10:02 OPEN rev12 -> fresh epoch 12
10:03 B fires -> cannot complete old A->B; a new A in epoch 12 is required
```

This reset applies only before MATCHED has created a `decision_cycle_id`. Once a cycle exists, subsequent Coins CLOSE/OPEN revisions do not alter that cycle, its pinned configuration, accepted/placed order, pending-order monitor or Frozen Condition. Those continue under normal lifecycle terminal rules.

### 2.2 Pending-order activation input from Order Lifecycle

When an approved pending LIMIT order has actually been placed/accepted, Order Lifecycle sends:

```text
Order Placed
```

Minimum activation identity:

```text
decision_cycle_id
set_result_id
position_plan_id
tranche_id
symbol
order_id / client_order_link_id
order_placed_at
```

`Order Placed` does not ask Set to recalculate the trade.

It activates monitoring of the frozen Market Invalidation Inputs tied to the originating Set decision cycle.

---

## 2.3 Canonical decision-cycle correlation ID

A unique correlation ID is created by **Set**, not by Portfolio Rules.

Canonical field:

```text
decision_cycle_id
```

Creation rule:

```text
Set MATCHED
→ create new decision_cycle_id
```

The ID identifies one concrete downstream trade-decision attempt that originated from one specific matched market configuration.

It is created only when Set has a valid matched configuration that is handed to Position Rules.

It is not created for:

```text
Set = NONE
Set = UNAVAILABLE
Set not yet matched
```

Canonical propagation:

```text
Set
  → Position Rules
  → Order Lifecycle
  → Set
```

The same `decision_cycle_id` must be preserved without mutation across all downstream messages belonging to that attempt.

The correlation chain is:

```text
decision_cycle_id
+
set_result_id
+
position_plan_id
+
tranche_id
+
order_id / client_order_link_id
```

Only `decision_cycle_id` is the cross-component correlation key.

The other identifiers identify domain-specific objects created later in the lifecycle.

Set uses `decision_cycle_id` to match a later `Order Placed` event back to the exact frozen Market Invalidation Inputs created for the originating matched setup.

Portfolio Rules may receive or persist `decision_cycle_id` inside downstream audit/event records, but Portfolio Rules is not its owner and must not rely on it for portfolio-allocation logic.

---

## 3. Set responsibilities

Set owns all market-analysis logic.

### 3.1 Initial-analysis responsibilities

Set analyzes only symbols whose latest Portfolio Rules coin status is:

```text
OPEN
```

A symbol whose latest status is:

```text
CLOSE
```

must not be evaluated for a new trade opportunity.

Set is responsible for:
- evaluating approved Triggers;
- combining Triggers according to Set logic;
- evaluating temporal relationships;
- tracking Set formation state;
- determining whether the Set is matched;
- determining `LONG | SHORT | NONE`;
- producing a canonical match timestamp;
- producing the governed `Market Handoff` required by Position Rules;
- creating and retaining the frozen Market Invalidation Inputs for the matched Set result.

### 3.2 Pending-order monitoring responsibilities

After `Order Placed`, Set is responsible for:
- activating the frozen invalidation predicates for the specific `set_result_id / tranche_id`;
- obtaining the current market / derived metric values required by those predicates;
- evaluating only those frozen predicates;
- keeping monitoring internal while all conditions remain valid;
- emitting `Order Cancel Signal` when a hard invalidation condition becomes true;
- treating required market data as `UNAVAILABLE` under the F-013 reducer in Part IV §12A and the reconcile-first fail-safe in Part IV §17, using `Order Cancel Signal` cause `MONITORING_UNAVAILABLE` on the same Set → Order Lifecycle boundary.

Set is not responsible for:
- determining portfolio allocation need;
- deciding requested tranche capital;
- determining leverage;
- submitting orders;
- cancelling an order directly on the exchange;
- calculating final Entry / TP / SL values;
- managing fills;
- managing portfolio reservations;
- managing open positions.

Order cancellation execution belongs to Order Lifecycle.

---

## 4. Set outputs

Set has two distinct output contracts.

### 4.1 Initial-analysis outputs

Set evaluation may end without creating a trade-decision cycle.

If no directional Set is matched, Set records an evaluation result only:

```yaml
set_evaluation:
  symbol:
  set_id:
  set_version:
  matched: false
  direction: NONE
  evaluated_at:
  rejection_diagnostics:
```

For:

```text
NONE
UNAVAILABLE
not yet matched
```

Set does **not** create:

```text
decision_cycle_id
set_result_id
Market Handoff
```

When a directional Set is matched:

```text
matched = true
direction = LONG | SHORT
```

Set creates a fresh:

```text
decision_cycle_id
set_result_id
```

Canonical matched output:

```yaml
set_result:
  decision_cycle_id:
  set_result_id:
  symbol:
  set_id:
  set_version:
  core_set_id:
  matched: true
  direction: LONG | SHORT
  matched_at:
  matched_constituents:
    - core_set_constituent_id:
      trigger_id:
      trigger_version:
      trigger_occurrence_id:
      references:
        - reference_key:
          indicator_id: null
          timeframe:
          level_id:
  resolved_reference_bindings: []
  frozen_condition_record_id:
  market_handoff_message_id:
```

The `decision_cycle_id` is propagated unchanged downstream and is the canonical cross-component correlation key for that concrete trade-decision attempt.

Only the matched `Set Result + Market Handoff` travels to Position Rules.

**Market Invalidation Inputs do not travel to Position Rules.**

They remain internal Set state tied to the originating `decision_cycle_id + set_result_id`.

### 4.2 Pending-order monitoring output → Order Lifecycle

Set emits no message while validity is VALID and no previously established
sticky cancellation requirement remains outstanding. Replaying an outstanding
requirement is not a KEEP message or a new invalidation evaluation.

The existing `ORDER_CANCEL_SIGNAL` family/version 2 has two explicit causes.

For a TRUE frozen hard invalidator:

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

For the separate UNAVAILABLE fail-closed requirement:

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

Semantically both causes use only:

```text
Set → Order Lifecycle
Order Cancel Signal
```

Order Lifecycle owns reconciliation, the actual cancel request and exchange
confirmation. INVALIDATION retains its original evidence-effective
`invalidated_at`, exact frozen record/predicate/evidence and replay identity.
MONITORING_UNAVAILABLE carries a truthful sticky requirement, not TRUE
invalidation evidence. Receipt of that cause requests reconciliation first;
only authoritative proof of a still-active unfilled remainder permits the
cancel-required execution step. Known terminal proof suppresses a new request;
a terminal race makes an already delivered request idempotently inapplicable.

Part IV §12A and the Semantics section of
[`ORDER_CANCEL_SIGNAL.md`](../business-contracts/ORDER_CANCEL_SIGNAL.md)
define requirement identity, effective time, unavailable reasons, unresolved
activation handling and replay. Part IV §17 retains outage behavior. Neither
cause closes filled exposure or authorizes Portfolio release.

---

## 5. Direction belongs to Set

Market direction is a Set responsibility.

Portfolio Rules do not determine LONG or SHORT.

Position Rules do not independently infer or reverse the direction.

A matched Set must emit exactly one deterministic direction:

```text
LONG
SHORT
```

For Sets governed by F-005, final direction is owned by the classifier and final resolution in Part II §§33–37. A fixed direction label or matched-branch label cannot bypass, override or reverse F-005. F-001 sign evidence, F-002 participation and F-003 volatility are not final direction decisions.

Outside that F-005-governed scope, existing generic deterministic Set definitions may fix direction or determine it explicitly from the matched branch; their existing conflict-resolution requirements remain. Within F-005 scope, any rule arbitrating multiple eligible Core Sets must be deterministic, Set-owned and consistent with F-005; missing/conflicting arbitration makes configuration ineligible. No first-arrival, lexical or strongest-score rule is introduced here.

A Set must not rely on its human-readable name to imply direction.

If conflicting branches can resolve to LONG and SHORT at the same canonical timestamp, the Set definition must contain deterministic conflict resolution or it is invalid.

---

## 6. Market Handoff

Set passes the frozen initial market-analysis payload to Position Rules.

Canonical flow:

```text
Portfolio Rules
→ Coins
→ Set
→ Market Handoff
→ Position Rules
```

The Market Handoff contains the governed market facts required for initial trade construction, including the already-approved:
- immutable direction;
- identity and timestamps;
- market reference geometry;
- volatility;
- `entry_context`;
- `sl_context`;
- `tp_context`;
- instrument price geometry required by Position Rules.

Canonical metric definitions and analytical semantics remain Set-owned in this document's Part II §§5–27 and Part III §10, [ATR semantics](#10-atr-semantics). The [Set numeric policy](../schemas/SET_NUMERIC_POLICY.md), §§1–5, governs deterministic computation and serialization. [Market Data Request](../api-contracts/MARKET_DATA_REQUEST.md), §§3–5 and §7, governs the normalized factual market-data inputs, their timestamps, availability and completeness.

Position Rules must not call back into Set to reconstruct or reinterpret the original match.

### Hard exclusion

The following are **not** part of the Position Rules Market Handoff:

```text
Market Invalidation Inputs
pending-order monitoring state
Order Cancel Signal
live pending-order validity status
```

These remain Set-owned runtime state.

---

## 7. Dynamic position inputs — synchronized status

The previously pending Dynamic Entry / Dynamic Stop Loss / Dynamic Take Profit input requirements have now been defined by approved downstream methodologies and Set Handoff amendments.

The canonical Set → Position Rules handoff is governed by:

```text
TRIGGERTRADE_DYNAMIC_POSITION_INPUTS_SET_HANDOFF_CONTRACT
+
Entry Context Amendment
+
SL Context Amendment
+
TP Context Amendment
```

Set provides only governed market-analysis inputs.

Set does not calculate:
- final Entry;
- final Stop Loss;
- final Take Profit;
- quantity;
- leverage;
- trade economics.

Those remain Position Rules responsibilities.

---

## 8. Trigger composition

A Set is composed only from approved Triggers.

The Set must not hide new metric conditions inside prose or Set operators.

If a new atomic market test is required, it must first be an explicitly governed, versioned Trigger. The generic Trigger-result and Trigger-event contract required by the Set engine is defined in Part I §§10–12 and §17 of this document. No external Trigger Contract is needed to implement these semantics; concrete configured market predicates remain separate from this generic contract.

---

## 8A. F-001 — Signed 1m endpoint price displacement

### Exact formula and role

Definitions:

```text
price_basis = trade-price-derived KLINES.close
timeframe = 1 minute
reference_price = close of the immediately preceding completed 1m candle
observed_price = close of the current completed 1m candle
```

Working displacement:

```text
move_pct_work =
Q36(100 * (observed_price - reference_price) / reference_price)
```

Predicate:

```text
trigger_true = abs(move_pct_work) >= theta_move_pct
```

Comparison is exact and inclusive. The numerical value `1` means one percent.

### Inputs

| Input | Requirement |
|---|---|
| Venue/product/instrument | Same bound source, product and instrument for both candles. |
| `reference_price` | `KLINES.close` of the immediately preceding completed 1-minute candle. |
| `observed_price` | `KLINES.close` of the current completed 1-minute candle. |
| Candle completion evidence | Both candles completed and source-final under governed market-data selection. |
| Evaluation slot | Current completed 1-minute slot. |
| `theta_move_pct` | Mandatory positive pinned research parameter in percent units. |
| Freshness policy | `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for active Set formation epoch. |
| Source coverage/finality | Complete selected KLINES coverage and no unresolved contradiction. |

### Outputs

| Output | Requirement |
|---|---|
| Trigger result | `TRUE`, `FALSE` or `UNAVAILABLE`. |
| Arithmetic status | `AVAILABLE` or `UNAVAILABLE`. |
| `move_pct_work` | Signed Q36 working percent displacement when arithmetic status is `AVAILABLE`; otherwise unavailable. |
| Sign evidence | `UP`, `DOWN`, `FLAT` when arithmetic status is `AVAILABLE`; otherwise unavailable. |
| Trigger-result status reason | Reason code for `UNAVAILABLE`, if applicable. |
| Effective slot | Current completed 1-minute slot. |
| Freshness policy/version | `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`. |
| Role satisfaction | CURRENT_STATE only for the current completed 1-minute slot. |

Sign evidence:

```text
UP   if move_pct_work > 0
DOWN if move_pct_work < 0
FLAT if move_pct_work = 0
```

F-001 does not emit LONG or SHORT.

### Units

Prices are exact decimal price values in source KLINES units for the same
instrument. `move_pct_work` and `theta_move_pct` are percent units where `1`
means one percent.

### Parameters

| Parameter | Class | Requirement |
|---|---|---|
| `theta_move_pct` | RESEARCH_PARAMETER | Mandatory, positive, pinned for active Set/Trigger configuration. |
| Timeframe | Fixed product decision | 1 minute. |
| Price basis | Fixed product decision | Trade-price-derived KLINES close. |
| Freshness policy | Fixed configuration contract | Current completed 1-minute slot membership only. |

The threshold value remains configurable; this rule does not select or optimize it.

### Domain and preconditions

F-001 can evaluate only when:

1. The symbol is in active Set analysis scope for the active formation epoch.
2. The Trigger configuration and `theta_move_pct` are pinned.
3. Current and preceding 1-minute KLINES candles are selected from the same
   venue/product/instrument and factual source.
4. Both candles are completed, source-final, within the evaluation cutoff, and
   have complete coverage.
5. `reference_price > 0`.
6. `observed_price >= 0`.
7. Price values are finite exact decimals with no NaN, infinity, binary float
   conversion or inferred fallback.
8. No unresolved source contradiction or identity mismatch exists.
9. The persisted freshness policy is
   `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`.

Missing intervals cannot be bridged by choosing an older reference.

### Missing and invalid behavior

| Case | Arithmetic status | `move_pct_work` / sign evidence | Trigger result |
|---|---|---|---|
| Missing current or reference candle | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Incomplete/still-forming candle | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Mismatched venue/product/instrument/source | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Missing source finality or incomplete coverage | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| `reference_price <= 0` | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Invalid, NaN, infinite or binary-float-derived price | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Missing, zero or negative `theta_move_pct` with otherwise valid arithmetic inputs | `AVAILABLE` | Computed and retained as non-satisfying diagnostic evidence | `UNAVAILABLE` |
| Missing, zero or negative `theta_move_pct` with invalid arithmetic inputs | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Missing/unknown freshness policy version | Depends on arithmetic inputs | Arithmetic may be retained if otherwise valid | `UNAVAILABLE` |
| Source contradiction | `UNAVAILABLE` / reconciliation-blocked | Unavailable | `UNAVAILABLE` |
| Valid zero observed price with valid reference and threshold | `AVAILABLE` | `-100%`, `DOWN` | Predicate result by threshold |

Absent arithmetic evidence must never become fabricated zero, `FLAT`, or a
previous value. Retained diagnostics cannot satisfy CURRENT_STATE while the
Trigger result is `UNAVAILABLE`.

### Boundaries

Equality passes:

```text
abs(move_pct_work) = theta_move_pct -> TRUE
```

Below threshold fails:

```text
abs(move_pct_work) < theta_move_pct -> FALSE
```

Zero movement:

```text
move_pct_work = 0
sign_evidence = FLAT
trigger_true = false
```

for every valid positive threshold.

Valid observed zero produces exactly `-100%` and `DOWN`; the predicate result
depends on the pinned threshold. If that zero becomes the next reference, the
next evaluation is `UNAVAILABLE` because `reference_price <= 0`.

### Precision and rounding

Evaluate subtraction, multiplication and division exactly according to
`TT_SET_NUMERIC_V1` / N-008 principles. Apply exactly one named working
quantizer:

```text
Q36 = 36 fractional decimal places, ROUND_HALF_EVEN
```

Q36 retains integer digits. Quantization precedes both sign evidence and
threshold comparison.

The predicate compares:

```text
abs(move_pct_work) >= theta_move_pct
```

with no epsilon, no intermediate rounding, no binary float conversion, no
display-rounded gate and no additional threshold quantizer.

### Time semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`:

- observed candle is the completed 1-minute candle for `S`;
- reference candle is the immediately preceding completed 1-minute candle.

The result is valid only for the current completed 1-minute slot.

### State, replay and restart

F-001 is a CURRENT_STATE Trigger. It is satisfied only when:

```text
trigger_result == TRUE
AND arithmetic_status == AVAILABLE
AND freshness_policy_version == F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
AND evaluation_slot == requested_current_slot
```

Freshness policy:

```text
F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
fresh_for_slot(evaluation_slot, requested_current_slot)
= evaluation_slot == requested_current_slot
```

There is no additional timeout, grace period, wall-clock age, scheduler-age or
receipt-time freshness condition.

Set derives the requested slot from its governed completed-minute evaluation,
not receipt, restart or scheduler time. Restart restores the persisted slot and
compares it to the currently requested slot; restart does not renew freshness.

### Configuration pinning

F-001 material configuration includes:

- Trigger ID/version;
- price basis;
- timeframe;
- endpoint selection;
- `theta_move_pct`;
- CURRENT_STATE role;
- freshness policy version
  `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`;
- numeric policy.

Started Set formation epochs use the pinned configuration selected for that
epoch. Later edits apply only to future epochs/cycles.

F-001 is signed endpoint displacement, not an ATR-normalized return. F-003 is separate volatility context and is not an arithmetic operand of F-001. F-001 neither selects LONG/SHORT nor changes the Market Handoff match-reference price. Preserve the generic Trigger epoch, freshness, event and consumption rules in Part I §§10–12 and §17; the concrete F-001 role is CURRENT_STATE only. Retain the exact endpoint prices, candle and source identities/revisions, coverage/finality evidence, effective slot, arithmetic/Trigger statuses and reasons, Q36 output/sign, formation epoch and pinned configuration/numeric policy. Repeated identical evidence is idempotent; conflicting accepted evidence follows existing integrity handling and cannot rewrite a frozen handoff.

---

## 8B. F-002 — Futures relative participation confirmation

### Exact formula and role

Definitions:

```text
market = Bybit USDT linear perpetual futures
volume_basis = exchange KLINES.volume in base-coin units
timeframe = 1 minute
c = current completed 1m candle volume
v(1)..v(60) = immediately preceding 60 completed 1m candle volumes
```

Sort historical values ascending:

```text
v_sorted(1) <= ... <= v_sorted(60)
```

Median:

```text
M = (v_sorted(30) + v_sorted(31)) / 2
```

Rank:

```text
K = count(v(i) <= c)
```

Relative volume and rank percent:

```text
R = c / M
P = 100 * K / 60
```

Predicate:

```text
trigger_true = (R >= 2) AND (P >= 90)
```

Equivalent valid-domain boundary:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

This equivalent boundary may be used only after establishing `M > 0`.

### Inputs

| Input | Requirement |
|---|---|
| Venue/product/instrument | Bybit USDT linear perpetual futures, same instrument and factual source across all candles. |
| `c` | Exchange KLINES.volume in base-coin units for the current completed 1-minute candle. |
| Historical population | Exactly 60 immediately preceding completed consecutive 1-minute KLINES.volume values. |
| Candle identities | Persisted source identities/revisions for current and historical candles. |
| Evaluation slot | Current completed 1-minute slot. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for the active Set formation epoch. |
| Source coverage/finality | Complete selected KLINES coverage and no unresolved contradiction. |

### Outputs

| Output | Requirement |
|---|---|
| Trigger result | `TRUE`, `FALSE` or `UNAVAILABLE`. |
| `M` | Trigger-local median baseline. |
| `K` | Trigger-local integer rank count. |
| `R` | Trigger-local relative-volume intermediate. |
| `P` | Trigger-local empirical-rank percent intermediate. |
| Effective time | Current completed 1-minute slot/evaluation timestamp. |
| Role satisfaction | CURRENT_STATE only for the current completed 1-minute slot. |

`M`, `K`, `R` and `P` are not exported Set metrics unless a later certified
formula or handoff contract explicitly exposes them.

### Units

All volumes are exchange KLINES base-coin units for the same Bybit USDT linear
perpetual futures instrument.

Do not substitute:

- quote turnover;
- contract count;
- raw-trade notional;
- spot-market volume.

`R` is dimensionless. `P` is percent units.

### Parameters

| Parameter | Approved value |
|---|---|
| Market | Bybit USDT linear perpetual futures |
| Volume basis | KLINES.volume in base-coin units |
| Timeframe | 1 minute |
| Historical population | 60 immediately preceding completed candles |
| Relative threshold | `R >= 2` |
| Rank threshold | `P >= 90`, equivalently `K >= 54` |
| Trigger role | CURRENT_STATE |
| Ordinary 30-day/14-day baseline | NOT_APPLICABLE |

These fixed predicate boundaries do not establish profitability or parameter optimality.

### Domain and preconditions

F-002 can evaluate only when:

1. The symbol is in active Set analysis scope for the active formation epoch.
2. The Trigger configuration is pinned.
3. The current candle and all 60 historical candles are selected from the same
   Bybit USDT linear perpetual futures instrument and factual source.
4. All 61 candles are completed, consecutive, source-final, within the
   evaluation cutoff, and have complete coverage.
5. Every volume is a finite exact nonnegative decimal in base-coin units.
6. `M > 0`.
7. No unresolved source contradiction, identity mismatch or basis mismatch
   exists.

### Missing and invalid behavior

| Case | Required behavior |
|---|---|
| Missing current candle | `UNAVAILABLE`. |
| Fewer than 60 immediately preceding candles | `UNAVAILABLE`. |
| Non-consecutive historical population | `UNAVAILABLE`. |
| Incomplete/still-forming candle | `UNAVAILABLE`. |
| Mismatched venue/product/instrument/source | `UNAVAILABLE`. |
| Missing source finality or incomplete coverage | `UNAVAILABLE`. |
| Invalid, negative, NaN, infinite or binary-float-derived volume | `UNAVAILABLE`. |
| `M = 0` | `UNAVAILABLE`. |
| Source contradiction | `UNAVAILABLE` / reconciliation-blocked; do not substitute stale data. |
| Valid `c = 0` with `M > 0` | `FALSE`. |

`UNAVAILABLE` is neither `FALSE` nor negative evidence.

### Boundaries

All comparisons are inclusive:

```text
R = 2 -> relative threshold passes
P = 90 -> rank threshold passes
K = 54 -> rank threshold passes
```

Ties count toward `K`.

Both thresholds must pass for `TRUE`. If either comparison fails and all
preconditions hold, the result is `FALSE`.

### Precision and rounding

Evaluate volumes as exact decimals under `TT_SET_NUMERIC_V1` / N-008
principles. Sorting is exact. `K` is an exact integer count. `R` and `P` are
exact rational/decimal trigger-local intermediates.

No epsilon, binary float, intermediate rounding, display-rounded comparison or
alternative threshold is permitted.

The division-free boundary can be used after `M > 0` is proven:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

### Time semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`:

- current observation is the completed 1-minute candle for `S`;
- historical population is the immediately preceding 60 completed consecutive
  1-minute candles `[S-60m, S)`.

The result is valid only for the current completed 1-minute slot. The next
1-minute boundary requires a new evaluation. Receipt time, scheduler time,
restart time and wall-clock loop time cannot substitute for the governed slot.

### State, replay and restart

F-002 is a CURRENT_STATE Trigger. It is satisfied only when the authoritative
result for the current completed 1-minute slot is `TRUE` and freshness remains
valid for that slot.

Persist:

- Trigger ID/version/configuration;
- symbol and active formation epoch;
- evaluation slot;
- current and historical candle identities/source revisions;
- volume basis;
- numeric policy;
- `M`, `K`, `R`, `P`;
- tri-state result.

Replay or restart must rehydrate accepted evaluation state and source
identities before accepting new evaluations. Duplicate identical evaluation is
a no-op. Conflicting source content or changed accepted values trigger
reconciliation/integrity handling and do not silently alter downstream frozen
handoffs.

Rehydration does not renew freshness.

### Configuration pinning

F-002 material configuration includes:

- Trigger ID/version;
- market/product;
- volume basis;
- timeframe;
- historical population count;
- thresholds `2` and `90`;
- CURRENT_STATE role;
- freshness policy;
- numeric policy.

Started Set formation epochs use the pinned configuration selected for that
epoch. Later edits apply only to future epochs/cycles.

F-002 confirms relative short-horizon futures participation only. It does not select LONG/SHORT, measure absolute liquidity or replace aggressive-flow imbalance. Its trigger-local population is not the ordinary 30-day/14-day normalization population and its base volume is not the quote-turnover input used by F-004. Existing generic Trigger epochs and event-consumption rules remain unchanged.

---

## 9. Boolean logic

Supported core relationships:

```text
AND
OR
NOT
```

Grouping must be explicit.

Example:

```text
TRG-A AND (TRG-B OR TRG-C)
```

Tri-state semantics:

### AND

```text
FALSE AND anything → FALSE
TRUE AND TRUE → TRUE
TRUE AND UNAVAILABLE → UNAVAILABLE
UNAVAILABLE AND UNAVAILABLE → UNAVAILABLE
```

### OR

```text
TRUE OR anything → TRUE
FALSE OR FALSE → FALSE
FALSE OR UNAVAILABLE → UNAVAILABLE
UNAVAILABLE OR UNAVAILABLE → UNAVAILABLE
```

### NOT

```text
NOT TRUE → FALSE
NOT FALSE → TRUE
NOT UNAVAILABLE → UNAVAILABLE
```

Missing evidence is not negative evidence.

---

## 10. Trigger result and event contract

This section is the complete generic state/event contract for existing configured Triggers. It defines no market predicate, signal, threshold or analysis heuristic. Set owns the evaluation records and event-consumption state; they are not a new business message or an API-owned trading decision.

### 10.1 Authoritative evaluation and tri-state result

A Trigger evaluation result is exactly `TRUE`, `FALSE` or `UNAVAILABLE`. `UNAVAILABLE` means that the result cannot currently be established from the required authoritative evidence. It is not equivalent to FALSE, must not be skipped when retaining the preceding state, and interrupts proof of a transition from an earlier known state. No implementation may infer a missing transition across an UNAVAILABLE interval.

An accepted evaluation is bound to the Trigger ID/version, symbol, active OPEN formation epoch, pinned Set/Trigger/Core Set configuration, exact evaluation as-of/selection and supporting source-evidence identities/revisions. Set retains an immutable evaluation identity or equivalent deterministic lookup key for that governed evaluation selection, with the result, effective timestamp and source contents immutably bound to it. Changing the claimed identity cannot bypass comparison against an already accepted exact selection/source binding. A duplicate delivery of the same evaluation is not a new evaluation. Same accepted identity with conflicting contents is retained as contradictory evidence under the existing evidence-ingestion and historical-data rules; it is not a new Trigger occurrence.

The authoritative effective timestamp of an evaluation is the governed market/evaluation instant at which the configured predicate is established from its selected evidence, subject to the existing completed-data, availability and as-of constraints. The result may not depend on evidence unavailable at that instant. For completed-bar inputs the governing completed-bar/evaluation selection must be explicit; for a multi-input Trigger the pinned definition must identify its governing evaluation selection. Neither an arbitrary constituent timestamp nor a receipt, processing, loop or restart time may replace it. This does not change any configured timeframe, horizon, predicate or data-selection rule.

Distinct evaluations are applied in their governed authoritative order within the same Trigger/formation epoch, not in delivery order. Set retains the selected evaluations and their source bindings so delayed input can be assembled in that order. A later TRUE cannot bypass a required unresolved predecessor or an UNAVAILABLE interval. An older delivery must not overwrite the current retained state or form an edge from the current state back to the past. Exact duplicates are no-ops; required ordering/continuity that cannot be proved makes edge-dependent evaluation UNAVAILABLE. Equal-time distinct evaluations need an authoritative ordering supplied by the governed evaluation/source selection; receipt order, database order and lexical identifiers are not substitute tie-breakers. Existing P16 historical-data eligibility and contradiction handling still apply before an unfinished formation can consume an event.

If no deterministic authoritative effective timestamp can be established, retain that limitation and the evaluation/evidence identity. Such a result cannot supply a FRESH_EVENT or a timestamp-dependent role. An UNAVAILABLE interruption is retained even when its effective timestamp is unavailable; absence of a timestamp is not permission to bridge it. No wall-clock timestamp may be fabricated to fill the gap.

### 10.2 CURRENT_STATE

`CURRENT_STATE(T)` is satisfied when the current authoritative result of T is TRUE and all other declared validity/as-of requirements hold. It requires no transition. FALSE does not satisfy it; UNAVAILABLE remains unavailable under §9 tri-state logic.

An initial authoritative TRUE, including the first valid TRUE after UNAVAILABLE, may establish CURRENT_STATE. This does not establish a fresh event. In particular, `UNAVAILABLE -> TRUE` may satisfy CURRENT_STATE but never creates FRESH_EVENT by itself.

### 10.3 FRESH_EVENT and unavailable interruptions

```text
FRESH_EVENT(T)
=
a newly accepted authoritative TRUE evaluation
whose immediately relevant retained prior Trigger result
in the same active formation epoch is an authoritative FALSE
```

The FALSE and TRUE must be distinct, authoritatively ordered evaluations. The immediately relevant prior result is the retained preceding evaluation state, including an intervening UNAVAILABLE; it is not the last known FALSE found by skipping unavailable results. An initial TRUE cannot supply its own missing predecessor. The resulting event is accepted once for that exact transition. Eligibility of that retained event for a formation role is additionally subject to its consumption state and the role's pinned freshness/window rules.

| Retained history within one active formation epoch | CURRENT_STATE at the last valid TRUE | Newly created FRESH_EVENT |
|---|---|---|
| No retained prior state -> TRUE | Satisfied | None |
| Initial state -> TRUE | Satisfied | None |
| FALSE -> TRUE | Satisfied | Exactly one, bound to that transition |
| UNAVAILABLE -> TRUE | Satisfied | None |
| FALSE -> UNAVAILABLE -> TRUE | Satisfied | None |
| TRUE -> UNAVAILABLE -> TRUE | Satisfied | None |
| UNAVAILABLE -> FALSE -> TRUE | Satisfied | Exactly one, at the new FALSE -> TRUE |
| TRUE -> TRUE | Satisfied | None |
| Replay of the same accepted TRUE | Unchanged | None; retain the original event/consumption record |
| Restart after event consumption | Restored from durable state | None; consumption remains recorded |

An evaluation from an older/superseded formation epoch cannot establish current state or a new event in the new epoch. A subsequent TRUE after an unavailable period requires a new authoritative FALSE followed by a later authoritative TRUE to create an event. A long-lived TRUE does not fire on every evaluation, re-arm or restart. `is_true(T)` denotes CURRENT_STATE; `fires(T)` denotes this FALSE -> TRUE event, never an implicit alternative transition policy.

### 10.4 Canonical event timestamp

For a proven FALSE -> TRUE transition, `event_at` is exactly the authoritative effective timestamp of the TRUE evaluation that proves it. It is not the FALSE timestamp, delivery time, processing time, Set loop time, restart time or current wall clock. Retain the effective timestamps exactly; do not round them before temporal comparisons.

If the TRUE evaluation lacks that deterministic timestamp, its FRESH_EVENT is unavailable. Re-observing TRUE after restart does not assign an event a new timestamp. A retained event's identity and `event_at` never change when its evidence is replayed. Section 17 defines how this timestamp governs event freshness and SINCE_SET_ARMED; §§11–12 govern sequence comparisons and windows.

### 10.5 Durable identity, consumption and restart

Before an evaluation or event can advance unfinished formation, Set durably retains, per Trigger in the active formation epoch:

- Trigger identity/version, symbol, exact OPEN `scope_revision` and pinned configuration identity/version/content digest;
- accepted evaluation identity/source binding, last accepted result including UNAVAILABLE, its authoritative effective timestamp when established, and retained predecessor/order evidence sufficient to reproduce the transition without bridging a gap;
- for each accepted FALSE -> TRUE, an immutable event identity or deterministic binding to the epoch, Trigger and exact FALSE/TRUE evaluation identities, plus its canonical `event_at`;
- whether and by which current formation/step the event has been consumed, with durable consumed-event deduplication state;
- the governing arming/evaluation anchors, configured window durations, exact derived freshness deadlines and partial-sequence state that depend on that event.

These are owner-local records. Their representation may use a persisted opaque ID or an equivalent immutable composite binding, but a fresh random ID on replay is not equivalent. Event identity includes the epoch and both evaluation identities, not merely symbol, TRUE value or a timestamp. This internal event binding does not move creation of the existing matched `trigger_occurrence_id`: P4 still binds concrete matched constituent occurrences and references at MATCHED.

Acceptance of an evaluation, recording its transition event, and advancing/consuming it in formation must be one durable atomic update, or staged without any visible formation effect until that complete update commits. MATCHED state, consumed-event bindings, cycle/result identities, frozen contexts and the existing Market Handoff outbox likewise commit together. A crash before commit has no visible formation/match effect; recovery repeats the same factual transition once. A crash after commit restores the same state/event/consumption record and republishes only the same committed handoff. It must not create another event or decision cycle.

Hydration restores retained Trigger results, interruptions, accepted-event identities, consumed flags and original deadlines before accepting new evaluations. Rebuilding from only the currently observed TRUE/FALSE value is forbidden. Consuming a retained event once does not consume it again on every TRUE evaluation or replay. An event that has not yet been consumed remains the same retained event, eligible only under its original epoch, time/window and formation rules; restart does not refresh it.

### 10.6 Formation reset and re-arm interaction

The §2.1A scope rule is unchanged. An effective newer Coins CLOSE resets unfinished pre-MATCH formation. A subsequent/newer effective OPEN creates a fresh formation epoch; a newer OPEN also supersedes unfinished older OPEN state even when an intermediate CLOSE is delayed. The new epoch begins with no retained prior Trigger state, event, consumption claim, freshness deadline or partial step from the old epoch. Historical records may remain for identity/evidence retention but cannot participate in new-epoch evaluation. No old FRESH_EVENT crosses the epoch boundary.

Within an epoch, an ordinary configured reset clears the current partial formation and its active step/window claims under §§18–19; it must not clear event-deduplication history or make a previously consumed transition fresh again. Re-arm follows the existing declared policy, does not infer a transition from current TRUE, and cannot erase a retained UNAVAILABLE interruption to reuse an earlier FALSE. Effective Coins scope revisions remain monotonic.

These pre-MATCH operations never reset an already-created `decision_cycle_id`, its immutable matched result/configuration, frozen invalidation state or an existing pending-order monitor. Delayed old-epoch observations and restart cannot reactivate an ended formation or synthesize a replacement match.

---

## 11. Sequence

The Set may define ordered sequences.

```text
TRG-A THEN TRG-B
```

Default semantics:

- A must satisfy its declared role first;
- B must satisfy its role strictly later than A;
- B occurring before A does not satisfy the sequence;
- equal timestamps do not satisfy `THEN` unless explicitly allowed.

For an event-style step, the step timestamp is the canonical `event_at` from §10.4. For a current-state step, it is the authoritative effective evaluation timestamp at which that declared role is satisfied. Comparisons use those exact timestamps, never arrival or processing order. A timestamp-dependent step whose governed timestamp is unavailable cannot complete the sequence.

---

## 12. Temporal windows

Example:

```text
TRG-A
THEN TRG-B WITHIN 10m
```

The pinned Set definition must explicitly identify the event/evaluation that starts the window. An event-started window uses that accepted event's `event_at`; a state/evaluation-started window uses the declared authoritative effective evaluation timestamp. Its persisted deadline is that exact anchor plus the configured duration. The existing window duration and boundary operator remain unchanged. No receipt/processing/restart time, current wall clock or inferred UNAVAILABLE -> TRUE event starts or restarts a window.

If B does not satisfy the step before the deadline, the active Set attempt follows its declared lifecycle behavior.

---

## 13. Maintained Trigger

Example:

```text
TRG-A
THEN TRG-B
WHILE TRG-C remains TRUE
```

TRG-C must remain TRUE for the specified period.

If it becomes FALSE or unavailable according to the Set definition, the current Set attempt follows its declared reset/expiry behavior.

---

## 14. Set-formation invalidation

A Trigger may invalidate an unfinished Set formation.

Example:

```text
TRG-A
THEN TRG-B
UNTIL TRG-X fires
```

This section describes **Set-formation invalidation** only.

It is distinct from the later pending-order `Market Invalidation Inputs`.

Set-formation invalidation answers:

```text
Should an unfinished Set attempt reset?
```

Pending-order market invalidation answers:

```text
Is an already placed pending LIMIT order still valid under the original market thesis?
```

Neither concept is a Stop Loss or an open-position exit rule.

---

## 14A. Market Invalidation Inputs for pending orders

For every matched Set result that can produce a pending LIMIT entry, Set must retain a frozen set of hard invalidation predicates.

The stored invalidation state must be keyed at minimum by:

```text
decision_cycle_id
set_result_id
symbol
```

These predicates belong to the originating market thesis.

They are not Position Rules fields.

They are not Order Lifecycle analytics.

The sole complete frozen-record definition is Part IV §12. Every applicable
Set version defines its own versioned hard conditions using that shape; the
record contains at least one valid deterministic condition with pinned
configuration identity/version/content digest and typed evidence selectors.
`set_result.frozen_condition_record_id` references that same
`market_invalidation.condition_record_id`; it is not a second record identity.

The specific conditions may differ by Set version, but their semantics are governed here and must be deterministic, frozen, auditable, and backtestable where applicable.

Binding baseline semantics:

```text
frozen at original Set result
no silent threshold drift
no auto-reprice
no chase
no KEEP signal
INVALID → Order Cancel Signal
```

Monitoring starts only after `Order Placed`.

Monitoring activates only after actual exchange acceptance/placement when:

```text
Order Placed.decision_cycle_id == frozen_condition.decision_cycle_id
AND
Order Placed.set_result_id == frozen_condition.set_result_id
AND
Order Placed.tranche_id is linked to that matched cycle
```

Set must not activate monitoring by symbol, order timestamp, nearest order,
latest Set result or current configuration. Ambiguous activation identity fails
closed and records an integrity/reconciliation condition; Set does not guess an
order.

Part IV §12A governs the exact VALID / INVALID / UNAVAILABLE / STOPPED reducer
and its output/action precedence. The record remains frozen at MATCHED; actual
activation is later and cannot be inferred from symbol or time.

### Pending-order monitoring stop invariant

Monitoring governs only the **active unfilled entry remainder** associated with the matched decision cycle.

Monitoring stops when authoritative Order Lifecycle state confirms that no active unfilled entry remainder remains because the entry order is:

```text
FULLY_FILLED
CANCELLED
REJECTED
SUBMISSION_FAILED
or otherwise confirmed terminal
```

For a partially filled entry:

```text
filled quantity
→ becomes real exposure governed by TP / SL / Manual Close

unfilled remainder
→ remains under Set pending-order monitoring
```

If Set emits `Order Cancel Signal`, monitoring remains logically pending until Order Lifecycle confirms a terminal cancel/fill outcome for the unfilled remainder.

Set must not infer terminal order state from market data.

Recommended monitor audit fields:

```text
monitor_started_at
last_validated_at
last_validation_state
monitor_stopped_at
monitor_stop_reason
```

---

## 15. Set lifecycle

### 15.1 Initial-analysis lifecycle

Canonical Set-formation states remain:

```text
INACTIVE
ARMED
PARTIALLY_MATCHED
MATCHED
EXPIRED
RESET
UNAVAILABLE
```

These states describe initial market-configuration formation.

`MATCHED` does not mean that an order was placed.

### 15.2 Pending-order monitoring lifecycle

Pending-order monitoring is a separate runtime mode attached to a matched `decision_cycle_id + set_result_id`.

Conceptual states:

```text
MONITORING_INACTIVE
MONITORING_ACTIVE
INVALIDATED
MONITORING_STOPPED
MONITORING_UNAVAILABLE
```

`MONITORING_ACTIVE` begins only after `Order Placed`.

`MONITORING_STOPPED` is entered only from authoritative Order Lifecycle state confirming that no active unfilled entry remainder remains. The Order Lifecycle contract must preserve the same `decision_cycle_id` correlation.

---

## 16. Set lifetime

A Set may define a maximum lifetime.

The Set must define what starts the lifetime clock:

- Set arming;
- first matched Trigger;
- other explicit Set-formation event.

No implicit clock-start semantics are allowed. The declared arming, Trigger or formation-event anchor uses its governed authoritative effective timestamp under §§10 and 17, not the time an evaluation loop happens to run or restart.

---

## 17. Trigger freshness

Canonical modes:

```text
CURRENT_STATE
FRESH_EVENT
SINCE_SET_ARMED
```

CURRENT_STATE and FRESH_EVENT are the distinct state/event roles defined in §10. SINCE_SET_ARMED is a temporal eligibility constraint on an explicitly declared state/event role, not a third way of manufacturing a transition. A Set using SINCE_SET_ARMED must specify whether the governed role is CURRENT_STATE or FRESH_EVENT; an omitted role is invalid configuration, not an implementer-selected default.

Set retains `armed_effective_at` for the current formation arming. The pinned arming rule must name its authoritative anchor: for an OPEN-driven arming, the `occurred_at` of that effective Coins OPEN; for a Trigger/evaluation-driven arming, the corresponding governed event/evaluation timestamp; for an explicitly configured session boundary, that boundary's governed timestamp. This does not change which arming/re-arm policy the Set uses. Missing or unprovable arming time makes SINCE_SET_ARMED and arming-dependent lifetime evaluation unavailable; current wall clock, first observation after restart and processing time are not fallbacks.

For SINCE_SET_ARMED with FRESH_EVENT, require a same-epoch, otherwise eligible canonical FALSE -> TRUE event with `event_at >= armed_effective_at`. For SINCE_SET_ARMED with CURRENT_STATE, require the authoritative current TRUE evaluation's effective timestamp to be `>= armed_effective_at`; it remains a state role and creates no event. In either case the governing timestamp may not be later than the authoritative as-of instant of the Set evaluation using it. The inclusive arming boundary does not override §11's strict THEN ordering or any explicitly configured window boundary.

A Set may also define a maximum acceptable age for a Trigger result. Event freshness uses the exact nonnegative difference between the consuming Set evaluation's authoritative as-of instant and the retained `event_at`. Current-state freshness uses the corresponding authoritative effective evaluation timestamp. A configured freshness deadline is the original event/evaluation anchor plus the pinned duration, with the declared boundary comparison; duration and operator must be explicit. Receipt, processing, restart and current wall-clock times never replace these anchors. Repeated TRUE observations do not refresh an old event's deadline.

All such timestamps and deadlines are persisted with the event/formation and restored unchanged. UNAVAILABLE -> TRUE supplies no event anchor for FRESH_EVENT, sequence-event or event-freshness logic. Old market events must not silently satisfy a Set intended to describe a current configuration. The separately governed Market Handoff `age_seconds = ceil(exact nonnegative timestamp delta in seconds)` rule is unchanged and is not a substitute for these exact temporal comparisons.

---

## 18. Reset

Reset clears the current partial Set formation.

Possible causes:

- reset Trigger;
- maintained Trigger failure;
- sequence timeout;
- Set expiry;
- session boundary where explicitly configured;
- unavailable required data;
- effective newer Coins CLOSE before MATCHED;
- creation of a newer OPEN formation epoch before MATCHED.

Reset affects unfinished Set formation only. Coins-driven reset never cancels or mutates a cycle after `decision_cycle_id` creation or an existing pending-order monitor.

---

## 19. Re-arm

Supported baseline policies:

```text
AFTER_RESET
AFTER_ALL_REQUIRED_TRIGGERS_CLEAR
NEXT_SESSION
```

Immediate re-arm is excluded from the baseline because it can create repeated matches from one long-lived TRUE configuration.

---

## 20. Active Set attempt

Baseline:

```text
one active initial Set formation state
per
set_id + set_version + symbol + effective OPEN formation_epoch(scope_revision)
while Coin status = OPEN
```

Parallel attempts are deferred unless a later methodology explicitly requires them.

---

## 21. N-of-M

Explicit N-of-M logic may be supported:

```text
AT_LEAST 3 OF [TRG-A, TRG-B, TRG-C, TRG-D]
```

It must be explicit.

N-of-M must not be represented by vague language such as:

```text
most conditions are bullish
```

---

## 22. Multi-timeframe Sets

Triggers preserve their own:

- timeframe;
- horizon;
- window;
- normalization;
- baseline.

A Set may combine multiple Trigger timeframes.

All values obey the in-package authoritative Trigger evaluation/event rules in Part I §§10–12 and §17, the completed-data/as-of requirements of the configured inputs and this document, and SYSTEM_PROTOCOLS P16 historical-data eligibility. No required behavior is delegated to an absent Trigger Contract.

No Set may use unavailable future information.

---

## 23. Set completion timestamp

Every match has one canonical:

```text
matched_at
```

For a sequential Set:

```text
matched_at
=
timestamp of final required Set step
```

For simultaneous Boolean logic:

```text
matched_at
=
first evaluation timestamp at which the complete Set expression is TRUE
```

The final-step or Boolean evaluation timestamp above is the governed authoritative event/evaluation timestamp defined in §§10–12 and §17, not receipt, processing or restart time. At `matched_at`, the Set also emits `direction`.

---

## 24. Set identity

Material Set identity includes:

- Set ID;
- version;
- Trigger IDs / versions;
- Boolean structure;
- sequence structure;
- state/event modes;
- time windows;
- freshness;
- expiry;
- reset;
- re-arm;
- N-of-M values where used;
- direction mapping;
- exact constituent/reference role bindings, indicator and timeframe provenance.

Changing a material component creates a new Set version.

---

## 25. No trade-construction or order-management Rules inside Set

A Set must not define:
- requested portfolio amount;
- requested tranche capital;
- leverage;
- final Entry;
- final TP;
- final SL;
- quantity;
- portfolio reservation;
- order submission mechanics;
- exchange cancellation mechanics;
- partial exits;
- trailing;
- re-entry.

Set's downstream/runtime responsibilities are limited to:

```text
INITIAL_ANALYSIS:
market match
+
market direction
+
Market Handoff

PENDING_ORDER_MONITORING:
frozen Market Invalidation Inputs
+
Order Cancel Signal when invalid
```

This does not make Set an order-management component.

Set decides market validity.

Order Lifecycle executes order-management actions.

---

## 26. Runtime auditability

For initial analysis, a Set Result must allow reconstruction of:

```text
Which symbol was OPEN for analysis when evaluation occurred?
Which Set/version was evaluated?
Which Triggers matched?
When did they match?
Which direction was emitted?
Which Market Handoff values were sent to Position Rules?
```

For pending-order monitoring, the audit trail must also allow reconstruction of:

```text
Which decision_cycle_id was created for the matched setup?
Which Order Placed event activated monitoring?
Which tranche/order was linked to which decision_cycle_id and set_result_id?
Which frozen invalidation predicates were active?
Which current market values were evaluated?
When did a predicate become invalid?
Which Order Cancel Signal was emitted?
```

---

## 27. Governance rules

1. Portfolio Rules owns the active coin-analysis scope.
2. `Coins` carries per-symbol `OPEN / CLOSE` status.
3. `OPEN` activates or preserves new-opportunity analysis for that symbol.
4. `CLOSE` stops new-opportunity analysis for that symbol.
5. Set must not independently add or remove symbols from the active analysis scope.
6. `CLOSE` does not terminate an already active pending-order monitor for an existing `decision_cycle_id`.
6A. Before MATCHED/`decision_cycle_id`, each effective OPEN `scope_revision` is a fresh formation epoch; a newer CLOSE resets unfinished formation and a newer OPEN starts with no carry-over.
6B. Set pins the exact Set/Trigger/Core Set configuration binding to the formation epoch/cycle; later configuration activation cannot alter that epoch or an already-created cycle.
7. Set does not determine portfolio need or capital allocation.
8. Set is composed only from approved Triggers and governed market-analysis logic.
9. Set determines market match.
10. Set determines `LONG / SHORT / NONE`.
11. Set outputs deterministic `matched_at`.
12. Set sends `Set Result + Market Handoff` to Position Rules.
13. Market Invalidation Inputs are not sent to Position Rules.
14. Position Rules does not call back into Set for initial trade construction.
15. Set does not calculate final Entry / TP / SL.
16. `MATCHED` is not a trade action.
17. Position Rules decides `APPROVE / REJECT`.
18. Set creates a unique `decision_cycle_id` only when a valid matched setup is handed downstream.
19. Portfolio Rules does not create or own `decision_cycle_id`.
20. Position Rules and Order Lifecycle must propagate `decision_cycle_id` unchanged.
21. Only after the order is actually placed does Order Lifecycle send `Order Placed` to Set.
22. `Order Placed` must carry the same `decision_cycle_id` and activates the matching frozen invalidation predicates.
23. Set performs the market-validity checks internally.
24. While valid, Set sends nothing.
25. When invalid, Set emits only `Order Cancel Signal`.
26. Set does not cancel exchange orders itself.
27. Order Lifecycle remains the owner of order management.
28. Missing market data remains distinguishable as `UNAVAILABLE`.
29. Look-ahead remains prohibited.
30. Frozen invalidation predicates must remain versioned/auditable.
31. No layer may silently take over another layer's responsibility.
32. Set owns no portfolio cooldown, reservation-release, tranche-slot-release, or Portfolio State mutation logic.
33. Pending-order monitoring stops only from authoritative Order Lifecycle terminal state for the unfilled remainder.
34. Unmatched evaluations create no `decision_cycle_id`.
35. Matched Set Results and Market Handoffs must carry `decision_cycle_id`.

---

# Part II — Direction Methodology

This Part incorporates the approved Direction Classifier methodology into the Set domain.

Binding interpretation:

```text
Direction = Set-owned market analysis
```

The classifier does not create an order and does not approve a trade.

Its result resolves into:

```text
LONG
SHORT
NONE
```

and participates in the Set Result / Market Handoff.

The technical formulas and deterministic rules below are preserved from the approved Direction Classifier specification.

# 3. Canonical time hierarchy

```text
HTF   = 1h
MID   = 15m
LOCAL = 5m
```

Secondary context:

```text
4h  = optional context
30m = optional context
```

Execution layer:

```text
1m / trade-level = excluded from core direction classification
```

No mandatory 1D directional gate exists.

Intraday classification does not imply forced closing at UTC day boundary.

---

# 4. Evaluation cadence and as-of semantics

The classifier evaluates:

```text
on every completed 5m bar
```

At evaluation timestamp `T`:

```text
5m inputs
= latest completed 5m observation at or before T

15m inputs
= latest completed 15m observation at or before T

1h inputs
= latest completed 1h observation at or before T
```

Still-forming 15m or 1h bars must never be used.

All rolling baselines also use observations that were fully available strictly before or at the evaluation timestamp according to the metric definition.

No future data may enter:

```text
metric values
swing confirmation
normalization baselines
percentiles
z-scores
benchmark context
```

---

# 5. Canonical price convention

For all return-based direction metrics:

```text
price_source = completed-bar close
```

Canonical return:

```text
RETURN(horizon=H)
=
Close_t / Close_(t-H) - 1
```

using completed observations only.

For:

```text
RELATIVE_RETURN(asset,BTC,15m)
=
RETURN(asset,15m)
-
RETURN(BTC,15m)
```

both legs must use aligned completed-bar close observations under as-of semantics.

---

# 6. Canonical normalization baseline

All ordinary rolling z-scores, ATR/volatility percentiles and other metrics explicitly reusing this baseline use the fixed **UTC analytical calendar**. UTC is system semantics, not a configurable Set parameter. Existing Set configuration pinning remains unchanged; no analytical-timezone configuration or wire field is introduced.

```text
lookback = 30 completed UTC calendar days
minimum_warmup = 14 completed UTC calendar days
mode = rolling
scope = same symbol
future observations = prohibited
```

This rule governs ordinary references to completed calendar days, N completed calendar days, minimum warmup in completed calendar days and ordinary rolling normalization populations, including every metric that explicitly reuses this baseline.

### UTC day and exact population interval

One analytical calendar day is the UTC half-open interval `[00:00:00Z, next 00:00:00Z)`. It is complete only when its exclusive UTC end boundary is at or before the governed evaluation cutoff. At an exact UTC midnight, the day ending at that instant is complete; the newly starting UTC day is the current incomplete day.

Let `evaluation_at` denote the existing governed, persisted analytical evaluation cutoff (`as_of` in Market Data Request), not request time, receipt time or restart time. This is explanatory notation, not a new field. Let `D` be `00:00:00Z` at the start of the UTC calendar day containing that cutoff. The N completed UTC calendar days immediately preceding that current incomplete day have the exact population interval:

```text
[D - N UTC calendar days, D)
```

For the ordinary 30-day lookback, use `[D - 30 UTC calendar days, D)`. For example:

```text
evaluation_at = 2026-09-14T06:00:00Z
D = 2026-09-14T00:00:00Z

canonical 30 completed UTC-day window:
[2026-08-15T00:00:00Z, 2026-09-14T00:00:00Z)
```

The current incomplete UTC calendar day must not enter this population, even when individual candles within it are already complete. The minimum 14-day warmup also counts only complete UTC analytical calendar days under the same boundary rule; the current incomplete day cannot contribute to that minimum. Lookback and warmup must not use different calendars.

This is not a trailing-720-hours window measured back from the cutoff, nor a local-timezone, account-timezone, Portfolio-accounting-day or exchange-session-day window. No ordinary normalization path may choose another timezone or substitute trailing hours for completed UTC calendar days.

### Observation membership and preserved temporal rules

Apply the existing dataset-specific membership rules using governed factual timestamps and the half-open UTC boundaries. Point events at the lower boundary are included and those at the upper boundary are excluded. Completed candle intervals and factual buckets must be wholly contained; a completed interval whose exclusive end equals the upper boundary is included. Associated candle-derived observations retain their governed completed-candle/series membership. See [Market Data Request](../api-contracts/MARKET_DATA_REQUEST.md), §§3 and 5.

Completed-candle requirements, source completeness, pagination/snapshot identity, source finality and no-future-data rules remain mandatory. The fixed UTC rule selects calendar boundaries only; metric formulas, percentile definitions, thresholds, lookback/warmup lengths and observation sampling rules remain unchanged. Recursive indicator ancestry remains distinct from the analytical population window.

An explicitly governed metric-specific temporal selector retains its own rule: Part II §8's UTC time-of-day/same-clock-bucket logic, Part III §19's previous-UTC-day structural reference and other explicitly defined reference boundaries are not replaced by this ordinary baseline. Portfolio accounting-day semantics are separate and unchanged.

Set selects this governed UTC analytical window and then expresses its exact boundaries as UTC `Z` timestamps in Market Data Request. UTC timestamp serialization alone does not select the analytical population. Persisted cutoff/selector identity, replay, restart and configuration binding retain their existing rules.

If fewer than 14 completed UTC calendar days are available:

```text
required normalized metric = UNAVAILABLE
```

and:

```text
direction = NONE
rejection_stage = DATA_UNAVAILABLE
```

**F-004 eligible completed days and leading initialization prefix.**

F-004 uses the eligible observations inside the ordinary 30-day interval. A day
is eligible for a metric's ordinary population only when the required factual
source coverage, source identity, finality, pagination/snapshot proof,
completed-candle or bucket membership, and all derived metric dependencies for
that day are available and contradiction-free.

If the instrument or required factual series has a proven inception later than
`D - 30 UTC calendar days`, the interval before inception is treated as proven
absence, not missing requested data. The population may contain 14 through 29
eligible completed UTC days in that initial-history case.

Partial inception days do not count for ordinary completed-day warmup. For each
metric, the first countable ordinary UTC day is the first complete UTC calendar
day that starts at or after the later of:

```text
instrument_or_series_inception_time
metric_source_series_inception_time
first_time_the_metric_can_have_all_required_derived_dependencies_available
```

rounded forward to the next UTC midnight if that later time is not already a
UTC midnight.

The leading interval before that first countable full UTC day is a proven
initialization prefix, not a missing-data gap, when its absence follows only
from instrument/series inception or from legitimate metric initialization
requirements such as canonical ATR seed formation. F-004 may exclude that
leading initialization prefix from the reference population. This exception is
only for the leading prefix before the first countable full UTC day. It does
not permit excluding, skipping or replacing any later unavailable observation
inside a countable day.

Canonical recursive dependencies still process their factual initialization
prefixes. For example, 5m ATR must preserve the seed candles and ordered ATR
ancestry through the prefix even though those pre-first-availability
observations are not countable VNM reference outputs. The population rule
selects eligible reference observations; it does not reset, reseed or discard
the recursive dependency.

Historical zero-close ATR_PCT observations and non-positive VNM denominators
remain unavailable outputs. If they occur inside the leading initialization
prefix before the first countable full UTC day, they are part of the startup
unavailability and are not reference observations. If they occur on or after
the first countable full UTC day, the affected metric is `UNAVAILABLE`; F-004
may not skip the day or shorten the population around it.

If the requested historical data should exist for a completed day but source
coverage, pagination, finality, continuity, identity or required derived-value
eligibility is missing or contradictory, that day is not silently skipped. The
affected F-004 metric is `UNAVAILABLE` until the source condition is resolved.

If fewer than 14 eligible completed UTC days are available after applying the
rules above:

```text
required normalized metric = UNAVAILABLE
directional classification support = unavailable to F-005
missing_reason = DATA_UNAVAILABLE
```

No expanding window, trailing-hours substitute, alternate timezone, omitted-gap
shortcut or current-day inclusion is permitted.

---

# 7. Z-score convention

The ordinary reference population uses [Part II §6's fixed UTC calendar](#6-canonical-normalization-baseline): a 30-completed-UTC-calendar-day lookback and a 14-completed-UTC-calendar-day minimum warmup. A metric with an explicitly separate temporal selector retains that selector.

Canonical:

```text
z = (x - μ) / σ
```

with:

```text
μ = rolling arithmetic mean
σ = rolling population standard deviation
ddof = 0
```

If:

```text
σ = 0
```

or the normalization is otherwise undefined:

```text
metric normalization = UNAVAILABLE
```

Baseline:

```text
no winsorization
no robust-z substitution
no expanding window
```

Normalized score clipping:

```text
clip(z / 2.0, -1, +1)
```

unless a metric has an explicitly different transform.

---

# 8. Time-of-day relative turnover baseline

Metric instance:

```text
TIME_OF_DAY_RELATIVE_TURNOVER(
    input_timeframe = 5m,
    timezone = UTC,
    lookback_days = 30,
    minimum_warmup_days = 14,
    baseline_statistic = median,
    same_clock_bucket = true
)
```

Example:

At:

```text
14:35–14:40 UTC
```

compare current 5m turnover to the median turnover of the same:

```text
14:35–14:40 UTC
```

bucket over prior completed eligible days.

The current observation never enters its own reference baseline.

Canonical ratio:

```text
TOD_REL_TURNOVER
=
current_5m_turnover
/
median_prior_same_clock_5m_turnover
```

If denominator is zero or undefined:

```text
UNAVAILABLE
```

Turnover basis:

```text
quote notional turnover
```

**Exact prior-bucket selection and median.**

The exact selector is the thirty prior completed eligible same-clock buckets
strictly before the current completed bucket. Let the current bucket be the
half-open interval:

```text
[bucket_start, bucket_end)
```

with `bucket_end <= evaluation_at`. The candidate reference buckets are the
same UTC clock bucket on the prior thirty UTC dates before `bucket_start`'s UTC
calendar date:

```text
[bucket_start - 1 UTC day, bucket_end - 1 UTC day)
[bucket_start - 2 UTC days, bucket_end - 2 UTC days)
...
[bucket_start - 30 UTC days, bucket_end - 30 UTC days)
```

The current bucket is excluded by the strict-prior rule even when `bucket_end`
is exactly UTC midnight. Therefore, for current bucket `[D - 5m, D)` at
`evaluation_at = D`, the reference set is the same `23:55-00:00 UTC` bucket on
the thirty preceding UTC dates:

```text
[D - 1 day - 5m, D - 1 day)
...
[D - 30 days - 5m, D - 30 days)
```

This metric-specific same-clock selector may reach one bucket whose start lies
before the ordinary `[D - 30 days, D)` day-window lower boundary at midnight.
That is intentional for `TOD_REL_TURNOVER` because SET defines it as a
same-clock lookback over prior completed eligible days, and the current
observation must never be included in its own baseline.

The same eligible-day rule in Part II §6 applies to same-clock references:

- proven pre-inception or leading-initialization absence may yield 14 through
  29 eligible prior same-clock observations;
- missing or contradictory evidence for a day that should exist makes the
  metric `UNAVAILABLE`;
- fewer than 14 eligible prior same-clock observations makes the metric
  `UNAVAILABLE`.

F-004 must persist the selected same-clock bucket identities, their UTC
intervals and their source coverage proof. Replaying the same cutoff must select
the same bucket identities.

For eligible references, compute the median exactly. With an even count, use
the exact arithmetic average of the two middle sorted values. If the median
denominator is zero or undefined:

```text
TOD_REL_TURNOVER = UNAVAILABLE
```

Otherwise:

```text
TOD_REL_TURNOVER =
current_5m_turnover / median_prior_same_clock_5m_turnover
```

---

# 9. Swing Point specification

Structure depends on confirmed swing points.

The first deterministic baseline uses symmetrical pivot parameters.

## 9.1 15m swing points

```text
input_timeframe = 15m
left_bars = 2
right_bars = 2
```

A swing high at bar `t` is confirmed only after bars:

```text
t+1
t+2
```

are completed.

Candidate rule:

```text
HIGH_t > HIGH_(t-1)
AND
HIGH_t > HIGH_(t-2)
AND
HIGH_t >= HIGH_(t+1)
AND
HIGH_t >= HIGH_(t+2)
```

A swing low:

```text
LOW_t < LOW_(t-1)
AND
LOW_t < LOW_(t-2)
AND
LOW_t <= LOW_(t+1)
AND
LOW_t <= LOW_(t+2)
```

---

## 9.2 1h swing points

```text
input_timeframe = 1h
left_bars = 2
right_bars = 2
```

Use the same comparison semantics.

---

## 9.3 Tie handling

For equal highs/lows:

```text
left side = strict comparison
right side = non-strict comparison
```

Purpose:

avoid marking multiple earlier equal-price bars as simultaneous independent pivots while allowing the candidate pivot to remain valid against equal later bars.

If multiple equal-price candidates remain possible under implementation edge cases:

```text
earliest confirmed qualifying pivot wins
```

---

## 9.4 Price tolerance

Baseline:

```text
equal_tolerance = 1 tick
```

Two levels are considered equal for structural comparison when:

```text
abs(level_a - level_b) <= instrument_tick_size
```

Tick size comes from exchange instrument metadata.

---

# 10. SWING_SEQUENCE_STATE specification

Use the two latest confirmed swing highs and two latest confirmed swing lows available as-of evaluation timestamp.

Let:

```text
H1 = previous confirmed swing high
H2 = latest confirmed swing high

L1 = previous confirmed swing low
L2 = latest confirmed swing low
```

Using 1-tick equality tolerance:

## BULLISH

```text
H2 > H1 + tick_size
AND
L2 > L1 + tick_size
```

Equivalent market description:

```text
higher high
+
higher low
```

## BEARISH

```text
H2 < H1 - tick_size
AND
L2 < L1 - tick_size
```

Equivalent:

```text
lower high
+
lower low
```

## AMBIGUOUS

Any other valid combination, including:

```text
HH + LL
LH + HL
approximately equal highs
approximately equal lows
```

## UNAVAILABLE

If fewer than:

```text
2 confirmed swing highs
or
2 confirmed swing lows
```

are available.

Structure state is calculated independently for:

```text
1h
15m
BTC 1h
```

---

# 11. DIRECTIONAL_EFFICIENCY specification

Metric instance:

```text
DIRECTIONAL_EFFICIENCY(
    input_timeframe = 15m,
    window = 8
)
```

This represents approximately:

```text
2 hours
```

of 15m observations.

Canonical formula:

```text
DE =
abs(Close_t - Close_(t-N))
/
sum(
    abs(Close_i - Close_(i-1))
    for i = t-N+1 ... t
)
```

where:

```text
N = 8
```

Range:

```text
0 ... 1
```

If denominator is zero:

```text
DE = 0
```

---

# 12. Directional Efficiency hard gate

Initial calibration:

```text
DE_MIN = 0.30
```

Rule:

```text
DE_15m < 0.30
→ NONE
```

Diagnostic:

```text
rejection_stage = DIRECTIONAL_EFFICIENCY_GATE
```

Post-gate modifier:

```text
DE_STRENGTH =
clip(
    (DE - 0.30) / 0.40,
    0,
    1
)
```

Thus:

```text
DE = 0.30 → 0
DE = 0.50 → 0.50
DE >= 0.70 → 1
```

---

# 13. ATR_PCT specification

Canonical ATR:

```text
input_timeframe = 15m
window = 14
smoothing = Wilder
```

True Range:

```text
TR_t =
max(
    High_t - Low_t,
    abs(High_t - Close_(t-1)),
    abs(Low_t - Close_(t-1))
)
```

Wilder ATR:

```text
ATR_14
```

Canonical percentage, only when current Q36 ATR work is available and the corresponding eligible completed 15m close is strictly positive:

```text
ATR_PCT_work = Q36(100 × ATR_work / Close_t)
ATR_15m_wire = Q18(ATR_work)
ATR_PCT_15m_wire = Q18(ATR_PCT_work)
```

Q36 and Q18 use HALF_EVEN under [Set numeric policy](../schemas/SET_NUMERIC_POLICY.md), §§3 and 5. `ATR_14` denotes the canonical persisted Q36 Wilder work state, not the Q18 export. The percentage is derived from work ATR, never from wire ATR; numerical `1` means one percent.

Require finite nonnegative factual prices and `0 <= Low <= Close <= High`, together with the unchanged source/identity/completion/cutoff/continuity proof. The factual predecessor close may lie outside the current range. Known historical identity/content checks precede malformed-candle rejection. An ineligible candle cannot advance state, be skipped or authorize reseeding.

For an otherwise eligible `Close_t = 0`, do not evaluate the ATR_PCT division: retain the ordinary exact TR, Q36 seed/recurrence update and zero predecessor for the next candle, but persist ATR_PCT `UNAVAILABLE` and emit no valid required handoff. Do not reset ATR, hold a stale percentage, substitute or clamp a value. Both Q18 exports must be strictly positive and available for a valid volatility handoff; zero or positive work rounded to zero remains ineligible without changing the work-state recurrence.

---

# 14. ATR percentile specification

Take the current:

```text
ATR_PCT(15m,14,Wilder)
```

and calculate its percentile rank against all completed same-symbol 15m ATR_PCT observations in the 30 completed UTC calendar days selected by [Part II §6](#6-canonical-normalization-baseline). The same fixed UTC boundary rule governs the 14-completed-UTC-calendar-day minimum warmup; this is not a trailing-hours population.

Baseline:

```text
not conditioned by time of day
```

Percentile empirical definition:

```text
percentile =
100 ×
count(reference_values <= current_value)
/
count(reference_values)
```

---

# 15. Volatility hard gate

Use the ATR percentile defined in Part II §14, with the ordinary fixed-UTC population and warmup from [Part II §6](#6-canonical-normalization-baseline).

Initial calibration:

```text
VOL_PERCENTILE_MIN = 15
VOL_PERCENTILE_MAX = 97
```

Rule:

```text
ATR percentile < 15
→ NONE

ATR percentile > 97
→ NONE
```

Diagnostic:

```text
rejection_stage = VOLATILITY_GATE
```

Market Handoff volatility context carries the governed baseline ATR and ATR_PCT fields, `volatility.atr_15m` and `volatility.atr_pct_15m`, as defined in [Market Handoff](../business-contracts/MARKET_HANDOFF.md) and the [strict wire schema](../schemas/wire.schema.json). ATR percentile remains Set-local for gate evaluation and, where retained, diagnostics or internal analysis. It is not a required baseline Market Handoff field, a Position Rules dependency or a new wire field. See also [Part III §11](#11-optional-volatility-regime-context).

---

# 16. VOLATILITY_NORMALIZED_MOMENTUM specification

The first baseline defines:

```text
VNM(H)
=
RETURN(H)
/
ATR_PCT_decimal
```

where ATR_PCT is converted from percent to decimal before division.

For example:

```text
ATR_PCT = 1.2%
ATR_PCT_decimal = 0.012
```

---

## 16.1 Primary 15m momentum

Metric instance:

```text
VOLATILITY_NORMALIZED_MOMENTUM(
    horizon = 15m,
    return_price = completed-bar close,
    volatility_metric = ATR_PCT,
    volatility_input_timeframe = 15m,
    volatility_window = 14,
    volatility_smoothing = Wilder
)
```

Then calculate rolling z-score over the canonical 30 completed UTC calendar days, with the 14-completed-UTC-calendar-day minimum warmup and exact boundary/membership rules from [Part II §6](#6-canonical-normalization-baseline).

Normalized:

```text
MOMENTUM_SCORE =
clip(momentum_z / 2.0, -1, +1)
```

---

## 16.2 Local 5m momentum veto instance

Metric:

```text
VOLATILITY_NORMALIZED_MOMENTUM(
    horizon = 5m,
    return_price = completed-bar close,
    volatility_metric = ATR_PCT,
    volatility_input_timeframe = 5m,
    volatility_window = 14,
    volatility_smoothing = Wilder
)
```

Use a separate same-symbol z-score baseline of completed 5m VNM observations over 30 completed UTC calendar days. The fixed UTC boundaries and 14-completed-UTC-calendar-day minimum warmup are those of [Part II §6](#6-canonical-normalization-baseline).

The local 5m VNM veto requires its own ATR_PCT instance:

```text
input_timeframe = 5m
window = 14
smoothing = Wilder
metric = ATR_PCT
```

This is the independent F-004-local 5m dependency. It uses the same exact-arithmetic, candle-eligibility and canonical-ancestry principles as [Set numeric policy](../schemas/SET_NUMERIC_POLICY.md), but retains a separate 5m series, anchor, seed and checkpoint. It is not the 15m F-003 output and does not become a certified 5m instance merely by referring to F-003. Its VNM observations and z-score population are the same-symbol 5m population specified here and in Part II §6.

For completed 5m candle `t`:

```text
TR_t = max(
    High_t - Low_t,
    abs(High_t - Close_(t-1)),
    abs(Low_t - Close_(t-1))
)
```

Canonical 5m seed:

```text
A_14_5m = Q36((TR_1 + TR_2 + ... + TR_14) / 14)
```

Canonical 5m recursive update:

```text
A_t_5m = Q36((13 * A_(t-1)_5m + TR_t) / 14)
```

When the current 5m ATR work state is available and the corresponding completed
5m close is positive:

```text
ATR_PCT_5m = Q36((100 * A_t_5m) / Close_t_5m)
ATR_PCT_decimal_5m = ATR_PCT_5m / 100
```

5m candle eligibility requires:

```text
0 <= Low <= Close <= High
```

with exact source identity, completed-only status, continuity, finality,
pagination/snapshot proof and canonical ordering. A factual predecessor close
need not lie inside the current candle range.

If a completed 5m candle is malformed, missing, incomplete, out of order,
contradictory, not final, or lacks the factual immediate predecessor close, the
affected 5m ATR/VNM computation is `UNAVAILABLE`. The ATR state does not
advance through that candle, the seed does not skip it, and no stale prior 5m
ATR_PCT may stand in for the current dependency.

If an otherwise eligible completed 5m candle has `Close_t_5m = 0`, the
`ATR_PCT_5m` quotient is not evaluated and `ATR_PCT_5m` is `UNAVAILABLE`. The
5m TR and ATR recurrence still preserve the factual candle and ancestry, as in
the F-003 zero-close pattern.

If `ATR_PCT_5m` is unavailable or `ATR_PCT_decimal_5m <= 0`, then `VNM_5m` and
the local momentum veto input are `UNAVAILABLE`.

5m ATR state must persist seed manifest, processed candle identities, prior
work value, source proof, numeric policy version and checkpoint digest. Restart
may restore only an authentic matching checkpoint and canonical subsequent
facts. Revised historical source content invalidates affected derived state and
does not authorize automatic correction acceptance, reseeding or reconciliation
release.

---

# 17. Momentum effective factor

Primary:

```text
MOMENTUM_SCORE
```

modified by directional efficiency:

```text
MOMENTUM_EFFECTIVE =
MOMENTUM_SCORE
×
(0.5 + 0.5 × DE_STRENGTH)
```

Range:

```text
[-1,+1]
```

---

# 18. Local momentum veto

Initial calibration:

```text
LOCAL_MOMENTUM_VETO_Z = 2.0
```

LONG prohibited if:

```text
VNM_5m_z <= -2.0
```

SHORT prohibited if:

```text
VNM_5m_z >= +2.0
```

This veto is evaluated only after hard gates pass.

---

# 19. Relative Strength specification

Canonical:

```text
RELATIVE_RETURN_15m
=
RETURN(asset,15m)
-
RETURN(BTC,15m)
```

Both use:

```text
completed 15m close
```

Normalize using [Part II §6's fixed UTC calendar and population boundaries](#6-canonical-normalization-baseline):

```text
same altcoin
rolling 30 completed UTC calendar days
15m observations
ddof = 0
minimum warmup = 14 completed UTC calendar days
```

Score:

```text
RELATIVE_SCORE =
clip(relative_return_z / 2.0, -1, +1)
```

---

# 20. Relative contradiction veto

Initial calibration:

```text
RELATIVE_Z_VETO = 2.0
```

LONG prohibited:

```text
relative_return_z <= -2.0
```

SHORT prohibited:

```text
relative_return_z >= +2.0
```

---

# 21. Aggressive Volume Delta specification

Metric:

```text
AGGRESSIVE_VOLUME_DELTA_PCT(
    horizon = 5m,
    quantity_basis = quote_notional
)
```

Let:

```text
AggBuyNotional
=
sum(notional of buyer-initiated trades)

AggSellNotional
=
sum(notional of seller-initiated trades)
```

Then:

```text
AGGRESSIVE_VOLUME_DELTA_PCT =
100 ×
(AggBuyNotional - AggSellNotional)
/
(AggBuyNotional + AggSellNotional)
```

If denominator is zero:

```text
UNAVAILABLE
```

Aggressor classification consumes the normalized `RAW_TRADES.data[].taker_side` (`BUY` for buyer-initiated trades, `SELL` for seller-initiated trades) and `notional_quote` defined in [Market Data Request §7, `MARKET_DATA_REQUEST.response`](../api-contracts/MARKET_DATA_REQUEST.md#market_data_requestresponse). That contract's §§3–5 govern factual timestamps, interval membership, availability and completeness. The metric formula is defined here in Part II §21; exact input parsing and arithmetic follow the [Set numeric policy](../schemas/SET_NUMERIC_POLICY.md), §§1–2.

---

# 22. Flow factor

```text
FLOW_RAW =
AGGRESSIVE_VOLUME_DELTA_PCT / 100
```

Participation adjusted:

```text
FLOW_EFFECTIVE =
FLOW_RAW
×
(0.5 + 0.5 × PARTICIPATION_STRENGTH)
```

No raw flow veto exists in v0.4.

---

# 23. Activity hard gate and modifier

From canonical:

```text
TIME_OF_DAY_RELATIVE_TURNOVER(5m)
```

Initial gate:

```text
ACTIVITY_MIN = 0.70
```

If:

```text
TOD_REL_TURNOVER < 0.70
```

then:

```text
NONE
rejection_stage = ACTIVITY_GATE
```

Post-gate:

```text
PARTICIPATION_STRENGTH =
clip(
    (TOD_REL_TURNOVER - 0.70) / 1.30,
    0,
    1
)
```

---

# 24. BTC structure specification

BTC uses the same:

```text
SWING_POINT(1h, left=2, right=2)
SWING_SEQUENCE_STATE
```

rules defined above.

Map:

```text
BULLISH   → +1
AMBIGUOUS → 0
BEARISH   → -1
```

---

# 25. BTC momentum specification

Metric:

```text
RETURN(BTC,15m)
```

using:

```text
completed 15m close-to-close
```

Normalize:

```text
BTC_RETURN_Z
```

using BTC's own completed-15m-return population over 30 completed UTC calendar days, with the 14-completed-UTC-calendar-day minimum warmup and fixed UTC boundaries from [Part II §6](#6-canonical-normalization-baseline).

Then:

```text
BTC_MOMENTUM_SCORE =
clip(BTC_RETURN_Z / 2.0, -1, +1)
```

---

# 26. BTC Context Score

```text
BTC_CONTEXT_SCORE =
0.60 × BTC_STRUCTURE_SCORE
+
0.40 × BTC_MOMENTUM_SCORE
```

Range:

```text
[-1,+1]
```

---

# 27. BTC contradiction veto

Policy:

```text
NON_CONTRADICTION_ONLY
```

Initial calibration:

```text
BTC_VETO_THRESHOLD = 0.70
```

LONG prohibited if:

```text
BTC_CONTEXT_SCORE <= -0.70
```

SHORT prohibited if:

```text
BTC_CONTEXT_SCORE >= +0.70
```

BTC contradiction does not force the opposite direction.

---

# 28. Structure Score

Inputs:

```text
SWING_SEQUENCE_STATE(asset,1h)
SWING_SEQUENCE_STATE(asset,15m)
```

Map:

```text
BULLISH   → +1
AMBIGUOUS → 0
BEARISH   → -1
```

Then:

```text
STRUCTURE_SCORE =
0.50 × STRUCTURE_1H
+
0.50 × STRUCTURE_15M
```

No active HTF structure hard veto exists in v0.4.

Structure expresses authority through:

```text
35% top-level weight
```

A future `STRUCTURE_STRENGTH` metric may support an extreme-structure veto after separate research.

---

# 29. Context-only derivatives evidence

The classifier records but does not score:

```text
OI_CHANGE_PCT(15m)
OI_CHANGE_PCT(1h)
FUNDING_RATE
PREMIUM_INDEX
MARK_INDEX_SPREAD_PCT
```

Where available, preserve:

```text
price direction
+
OI direction
```

joint state for later diagnostics.

Baseline:

```text
OI_WEIGHT = 0
FUNDING_WEIGHT = 0
PREMIUM_WEIGHT = 0
```

---

# 30. Other context-only evidence

Record where available:

```text
VWAP_DISTANCE
MARKET_BREADTH
RANGE_BOUNDARY
DISTANCE_TO_LEVEL
confirmed swing levels
```

These do not enter the v0.4 weighted Direction Score.

Relevant structural/volatility values may be handed downstream to Dynamic SL/TP.

---

# 31. Top-level weights

Canonical v0.4 calibration defaults:

```text
STRUCTURE            0.35
MOMENTUM             0.25
RELATIVE_STRENGTH    0.15
FLOW                  0.15
BTC_CONTEXT           0.10
```

Sum:

```text
1.00
```

---

# 32. Final Direction Score

```text
DIRECTION_SCORE =

0.35 × STRUCTURE_SCORE
+
0.25 × MOMENTUM_EFFECTIVE
+
0.15 × RELATIVE_SCORE
+
0.15 × FLOW_EFFECTIVE
+
0.10 × BTC_CONTEXT_SCORE
```

Range:

```text
[-1,+1]
```

---

# 33. Classification thresholds

Initial calibration:

```text
LONG_THRESHOLD  = +0.35
SHORT_THRESHOLD = -0.35
```

Decision:

```text
if hard gate fails:
    NONE

else:
    compute score

    if score >= +0.35:
        if LONG veto active:
            NONE
        else:
            LONG

    else if score <= -0.35:
        if SHORT veto active:
            NONE
        else:
            SHORT

    else:
        NONE
```

There is no forced opposite classification.

---

# 34. Veto set in v0.4

Active direction-specific vetoes:

```text
BTC contradiction veto
Relative contradiction veto
Local momentum contradiction veto
```

Disabled / not present:

```text
raw aggressive-flow veto
undefined strong-HTF-structure veto
OI veto
funding veto
premium veto
```

---


# 34A. Direction-to-Set resolution

Direction Classifier output is interpreted by the governing directional Set as follows:

```text
classifier_direction = LONG
→ directional criterion satisfied for LONG branch
→ if all other Set requirements are satisfied:
   matched = true
   direction = LONG
```

```text
classifier_direction = SHORT
→ directional criterion satisfied for SHORT branch
→ if all other Set requirements are satisfied:
   matched = true
   direction = SHORT
```

```text
classifier_direction = NONE
→ no directional branch is satisfied
→ matched = false
→ direction = NONE
```

A directional Set governed by this classifier may never emit:

```text
matched = true
direction = NONE
```

`classifier_direction` and final Set `direction` are distinct. Classifier `NONE` means no satisfied directional criterion. Classifier LONG/SHORT satisfies only that side's criterion; a final unmatched evaluation may still have `direction = NONE` because formation or mandatory handoff validation failed.

F-005 consumes the canonical Q36 F-004 score, all eleven required inputs and their required derived diagnostics, hard gates and both sides' veto evidence. Missing, malformed, contradictory or incompatible required evidence yields classifier `NONE` / `DATA_UNAVAILABLE`, even if a numeric score exists. In particular unavailable local 5m veto evidence is not false or neutral. Hard gates retain their inclusive passing boundaries. Scores `>= +0.35` produce a LONG candidate and scores `<= -0.35` a SHORT candidate; the open interval `(-0.35,+0.35)` is the dead zone. Only that candidate's BTC, relative and local-momentum vetoes can block it; an opposite-side veto never blocks or reverses the candidate.

Before `MATCHED`, the governing versioned Set expression must be authoritatively `TRUE`; the exact Core Set, constituent evidence, active formation epoch, pinned configuration, source/evaluation identities and applicable sequence, freshness, expiry, reset/re-arm and durable event-consumption conditions must be eligible. Required event evidence must be same-epoch and unconsumed. Event-dependent formation retains authoritative same-epoch `FALSE -> TRUE`, no bridging across `UNAVAILABLE`, and once-only consumption. `FALSE` or `UNAVAILABLE` cannot become a match.

Mandatory Market Handoff v4 identity, frozen snapshot/reference price, direction, positive required volatility, reference geometry and applicable binding/capability validation must pass before commitment. Classifier success followed by formation failure produces `matched=false`, final `direction=NONE` and a separate Set-resolution reason. Handoff-validation failure produces the same unmatched boundary with a separate handoff-validation reason. Neither path creates committed `decision_cycle_id`, `set_result_id` or a handoff.

Match state, consumption bindings, cycle/result identities, frozen contexts and handoff outbox commit together. Delivery failure after this commitment does not undo the match or mint new IDs: replay/retry restores and sends the same committed handoff. Preserve governed completed-5m analytical cadence, authoritative cutoff/match time and source selectors; receipt/restart/current time cannot replace them. Position may reject construction but cannot reinterpret or reverse the committed Set direction.

---

# 35. Required-data gate

Required for altcoin classification:

```text
asset structure 1h
asset structure 15m
DE 15m
VNM 15m
VNM 5m
relative return 15m
aggressive delta 5m
time-of-day relative turnover 5m
ATR_PCT 15m percentile
BTC structure 1h
BTC return 15m z-score
```

If a required item is unavailable:

```text
NONE
rejection_stage = DATA_UNAVAILABLE
```

Context-only metrics may be unavailable without failing classification.

---

# 36. Rejection diagnostics

Canonical primary values:

```text
NONE
DATA_UNAVAILABLE
DIRECTIONAL_EFFICIENCY_GATE
ACTIVITY_GATE
VOLATILITY_GATE
BTC_VETO
RELATIVE_VETO
LOCAL_MOMENTUM_VETO
SCORE_DEAD_ZONE
```

Every NONE must contain:

```text
primary_rejection_stage
```

Also store:

```text
all_failed_gates[]
all_active_vetoes[]
```

Canonical primary priority:

```text
DATA_UNAVAILABLE
→ DIRECTIONAL_EFFICIENCY_GATE
→ ACTIVITY_GATE
→ VOLATILITY_GATE
→ BTC_VETO
→ RELATIVE_VETO
→ LOCAL_MOMENTUM_VETO
→ SCORE_DEAD_ZONE
```

If several vetoes simultaneously block the candidate direction, preserve all in:

```text
all_active_vetoes[]
```

Retain every independently known failed hard gate in the canonical order, including `DATA_UNAVAILABLE` where applicable. An individual gate that cannot be evaluated is unavailable, not failed, passed or false.

`all_active_vetoes[]` contains only proven active vetoes against a trustworthy `candidate_side`, ordered BTC, relative, local momentum. Opposite-side vetoes are retained only as upstream evidence and cannot enter this candidate-filtered list. Without a trustworthy candidate, the list is empty with the explicit unavailable-score or dead-zone reason; unknown predicates are not fabricated false values. All six side-specific upstream predicates remain separately available as diagnostics.

For classifier success followed by formation/handoff failure, retain classifier direction and its diagnostics but record final `direction=NONE` and the separate Set-resolution/handoff-validation reason specified in §34A. Classification primary rejection and final-resolution failure are not conflated.

---

# 37. Set Result direction evidence

The ordinary `normalization.lookback_days: 30` and `minimum_warmup_days: 14` below mean completed UTC calendar days under [Part II §6](#6-canonical-normalization-baseline), including its exact population boundaries and membership rules. `mode: rolling` advances that governed completed-day population; it does not mean trailing hours. UTC is fixed system semantics, not an added direction-classifier or Set configuration parameter. Existing configuration pinning is unchanged.

Required audit payload:

```yaml
direction_classifier:
  id: TT-METH-014
  version: 0.4.1
  scope: ALTCOIN_VS_BTC

  evaluated_at:

  timeframes:
    htf: 1h
    mid: 15m
    local: 5m

  normalization:
    lookback_days: 30
    minimum_warmup_days: 14
    ddof: 0
    mode: rolling

  gates:
    data_available:
      passed:
      missing_inputs: []

    directional_efficiency:
      value:
      threshold: 0.30
      passed:

    activity:
      value:
      threshold: 0.70
      passed:

    volatility:
      atr_pct:
      percentile:
      allowed_range: [15, 97]
      passed:

  vetoes:
    btc:
      context_score:
      threshold: 0.70
      active:

    relative:
      z:
      threshold: 2.0
      active:

    local_momentum:
      z:
      threshold: 2.0
      active:

  factors:
    structure:
      htf_state:
      mid_state:
      normalized:

    momentum:
      raw:
      z:
      directional_efficiency_strength:
      effective:

    relative_strength:
      raw:
      z:
      normalized:

    flow:
      aggressive_delta_pct:
      participation_strength:
      effective:

    btc_context:
      structure_state:
      momentum_z:
      normalized:

  context:
    oi_15m:
    oi_1h:
    funding:
    premium:
    mark_index_spread:
    vwap_distance:
    market_breadth:
    swing_levels:
    range_boundaries:
    distance_to_levels:

  weighted_contributions:
    structure:
    momentum:
    relative_strength:
    flow:
    btc_context:

  score:
  direction:

  primary_rejection_stage:
  all_failed_gates: []
  all_active_vetoes: []
```

**F-004 working evidence and local diagnostic boundary.** Retain the analytical cutoff; source selector identities; manifests, selected-range coverage/finality evidence; numeric policy and upstream formula versions; configuration versions, thresholds and weights; ordinary population member identities and proven initialization boundaries; same-clock bucket IDs/UTC intervals/coverage; and local 5m seed/checkpoint ancestry. Retain current metric values, z-scores, percentiles, normalized Q36 factors, gates, all six side-specific veto predicates with values/thresholds/comparison directions/availability reasons, and Q36 `DIRECTION_SCORE`.

The six upstream predicates are:

```text
BTC_VETO_LONG
BTC_VETO_SHORT
RELATIVE_VETO_LONG
RELATIVE_VETO_SHORT
LOCAL_MOMENTUM_VETO_LONG
LOCAL_MOMENTUM_VETO_SHORT
```

They are separate from F-005's candidate-filtered `all_active_vetoes[]`. An unavailable predicate remains unavailable, not false. Required missing factors never become zero, neutral, stale values or redistributed weights.

The canonical score uses exact products and their exact sum before its single Q36 quantizer:

```text
DIRECTION_SCORE = Q36(
    0.35 * STRUCTURE_SCORE
  + 0.25 * MOMENTUM_EFFECTIVE
  + 0.15 * RELATIVE_SCORE
  + 0.15 * FLOW_EFFECTIVE
  + 0.10 * BTC_CONTEXT_SCORE
)
```

The separately retained weighted contributions are each Q36 of their named weighted factor and are diagnostic only. Their rounded sum, diagnostic Q18 exports or display rounding MUST NOT produce the score or feed a gate. Internal normalization remains Q36 under the unchanged numeric policy.

All this evidence is Set-local; it adds no Market Handoff metric or direction authority to F-004. Replay uses the same cutoff, selected members, canonical source ordering and authentic checkpoints. Duplicate identities do not add observations; changed accepted content invalidates affected eligibility rather than splicing history into frozen evidence.

**F-005 classifier and final-resolution evidence.** Preserve `candidate_side` (LONG, SHORT or absent when no trustworthy candidate exists), `classifier_direction`, final `matched`/`direction`, all classification availability/rejection diagnostics, separate formation/handoff-resolution reason, and all six upstream predicates. In the existing `direction_classifier` diagnostic object, `direction` describes classifier output; final match direction is recorded separately and is LONG/SHORT only for committed matched results.

Pin `direction_classifier_id = TT-METH-014`, version `0.4.1`, scope `ALTCOIN_VS_BTC`, the F-004 final specification identity, Set definition/version, Market Handoff version 4 and `TT_SET_NUMERIC_V1`. Preserve the governed analytical cutoff, selector identities, exact Core Set/constituent evidence, active formation epoch, required sequence/freshness/reset/re-arm/expiry state and consumption bindings. For a committed match, persist the same cycle/result IDs, frozen contexts and handoff outbox record atomically under §34A. Unmatched records contain no newly committed match IDs; delivery replay preserves committed IDs. These owner-local diagnostics add no handoff field.

---

# 38. Frozen-at-match invariant

When a Set reaches its canonical match timestamp:

```text
matched_at
```

freeze:

```text
direction
direction_score
raw factor snapshot
normalized factors
weighted contributions
gate outputs
veto outputs
reference levels used at match
```

Position Rules must not rewrite the historical classification.

Later market changes never rewrite the historical Market Handoff or frozen direction.

Before fill, Set may evaluate only the frozen Market Invalidation Inputs associated with that `decision_cycle_id`.

After fill, pending-entry monitoring no longer governs the filled exposure; the resulting position remains governed by TP / SL / Manual Close and Order Lifecycle.

---

# 39. Diagnostic score bands

For diagnostics only:

```text
+0.35 ... +0.55 → LONG
+0.55 ... +0.75 → STRONG_LONG
> +0.75         → EXTREME_LONG

-0.35 ... -0.55 → SHORT
-0.55 ... -0.75 → STRONG_SHORT
< -0.75         → EXTREME_SHORT
```

These labels:

```text
are not probabilities
do not change position sizing automatically
do not alter TP/SL automatically
```

unless a future Position Rules specification explicitly adopts them.

---

# Part III — Market Handoff Methodology

This Part incorporates the approved Set Market Handoff methodology.

The handoff is the immutable initial market-analysis payload sent:

```text
Set → Position Rules
Market Handoff
```

It is used by Position Rules for Entry / Stop Loss / Take Profit and feasibility calculations.

Hard boundary:

```text
Market Invalidation Inputs
≠ Market Handoff
```

Market Invalidation Inputs remain internal Set state and are never routed through Position Rules.

The approved technical handoff rules follow.

# 3. Snapshot invariant

Canonical:

```text
market_snapshot_at = matched_at
```

All Set-owned market inputs must satisfy:

```text
available_at <= matched_at
```

No still-forming candle, future-confirmed swing, later range, later VWAP state, or later normalization value may enter the handoff.

---

# 4. Direction invariant

For a matched directional Set:

```text
matched = true
direction = LONG | SHORT
```

If upstream Direction Classifier returns:

```text
NONE
```

then:

```text
matched = false
direction = NONE
```

and no initial Dynamic SL/TP Position Plan is produced from that Set result.

---

# 5. Required identity and audit fields

Canonical:

```yaml
identity:
  decision_cycle_id:
  set_result_id:
  symbol:
  set_id:
  set_version:
```

These are required for traceability and version provenance.

They do not themselves alter SL/TP geometry.

---

# 6. Required frozen snapshot fields

```yaml
snapshot:
  matched_at:
  market_snapshot_at:
  direction:
  set_match_reference_price:
```

All are universally required.

## `set_match_reference_price`

This is the canonical market price reference frozen at Set match.

Baseline factual basis:

```text
set_match_reference_price = TICKER.last_price
```

It is sampled from the same governed market snapshot used to declare MATCHED, with `observed_at <= matched_at`, and the handoff persists:

```text
reference_price_basis = LAST_TRADED_PRICE
reference_price_observed_at
reference_price_source
market_snapshot_id / response_id
```

If the configured basis or its required observation is unavailable, Set must not create a concrete handoff/cycle. It returns UNAVAILABLE rather than allowing Position Rules to choose another price source.

It is not:

```text
planned_entry_reference
actual_fill_price
```

Those are downstream-owned.

---

# 7. Universally required instrument geometry

Only the following price-mechanics field is universally required:

```yaml
instrument:
  tick_size:
```

`tick_size` is the canonical minimum legal price increment.

It is required for:

```text
level equality
distance interpretation
final downstream SL/TP rounding
```

The Set does not round hypothetical final SL/TP values.

---

# 8. Instrument audit metadata

May be included:

```yaml
instrument:
  contract_type:
  price_scale:
```

Roles:

```text
contract_type → audit/context
price_scale   → optional implementation metadata
```

Neither is a universal handoff-completeness blocker.

If an implementation requires `price_scale`, it may resolve it from the canonical instrument metadata source by `symbol`.

---

# 9. Universally required volatility scale

Canonical required package:

```yaml
volatility:
  atr_15m:
    value:
    input_timeframe: 15m
    window: 14
    smoothing: Wilder
    calculated_at:

  atr_pct_15m:
    value:
    input_timeframe: 15m
    window: 14
    smoothing: Wilder
    calculated_at:
```

Both are universally required.

---

# 10. ATR semantics

Canonical work state and Market Handoff values under [Set numeric policy](../schemas/SET_NUMERIC_POLICY.md), §§3 and 5:

```text
ATR_work = canonical Q36 ATR(window=14, smoothing=Wilder, input_timeframe=15m)
ATR_15m = Q18(ATR_work)
```

Only with available current work ATR and the corresponding eligible completed `Close_15m > 0`:

```text
ATR_PCT_work = Q36(100 × ATR_work / Close_15m)
ATR_PCT_15m = Q18(ATR_PCT_work)
```

Do not compute the percentage from already-exported `ATR_15m`. All current candle prices and the factual predecessor close must be finite/nonnegative; require `0 <= Low <= Close <= High`. A predecessor outside the current range is permitted. Known historical identity checks precede semantic rejection; an invalid candle cannot advance ATR, be skipped or trigger reseeding.

An otherwise eligible zero close still advances the prescribed TR/ATR state and remains the next predecessor, but its ATR_PCT is `UNAVAILABLE` without division. Persist the reason; no stale ratio, denominator substitution or reset is permitted. Both exported Q18 values must be strictly positive and available. Zero or a positive work value rounding to zero blocks handoff without clamping or modifying recurrence. Position consumes the exact received Q18 values, not recovered working precision.

The values must be fully available as-of `matched_at`.

---

# 11. Optional volatility-regime context

The following may be retained in Set-local diagnostics (not a baseline wire field). The optional ATR-percentile diagnostic reuses [Part II §§6 and 14](#6-canonical-normalization-baseline): `lookback_days: 30` and `minimum_warmup_days: 14` mean completed UTC calendar days under the same fixed, non-configurable ordinary analytical calendar.

```yaml
optional_context:
  volatility:
    atr_pct_percentile_15m:
      value:
      lookback_days: 30
      minimum_warmup_days: 14
      calculated_at:

    atr_5m:
    atr_pct_5m:
    atr_1h:
    atr_pct_1h:
    realized_volatility:
    volatility_ratio:
```

Roles:

```text
CONTEXT_ONLY
BOTH_OPTIONAL
JOINT_FEASIBILITY
```

`ATR_PCT_PERCENTILE_15m` is not a baseline Market Handoff completeness requirement or a Position Rules dependency. It remains Set-local where used for gate evaluation, diagnostics or internal analysis; it adds no wire field.

If this optional diagnostic is unavailable, baseline handoff completeness is unaffected. This does not relax the Direction Classifier's own required-data and volatility-gate rules in Part II §§14–15 and §35.

---

# 12. Canonical reference-level universe

The Set must provide one direction-neutral source of truth:

```yaml
references:
  levels: []
```

Each governed reference level exists once.

No separate authoritative:

```text
support_levels[]
resistance_levels[]
```

arrays exist in the canonical contract.

---

# 13. Required level object schema

Each `references.levels[]` item must contain:

```yaml
level_id:
level_type:
price:
timeframe:
formed_at:
confirmed_at:
available_at:
source_metric:
age_seconds:
```

Fields that do not apply to a level type may be:

```text
null
```

but `available_at` is always mandatory.

---

# 14. Canonical `available_at`

`available_at` is the timestamp at which the reference became legally usable in live evaluation.

Examples:

## Confirmed swing

```text
available_at = confirmed_at
```

## Previous-day high/low

```text
available_at = previous UTC day completed_at
```

## Governed range boundary

```text
available_at = range confirmation timestamp
```

## Other deterministic reference

Use the first timestamp at which all information required by its canonical definition was available.

Rule:

```text
available_at <= matched_at
```

must hold for every level in the handoff.

---

# 15. Canonical age

For the exact nonnegative timestamp delta define:

```text
age_exact_seconds = market_snapshot_at - available_at
age_seconds = ceil(age_exact_seconds)
```

The factual timestamps remain exact and are never rounded to obtain age. The integer wire field is a freshness/staleness metric and therefore must never understate actual age. Boundary examples:

```text
60.000000 seconds -> age_seconds = 60
60.000001 seconds -> age_seconds = 61
60.750000 seconds -> age_seconds = 61
```

Age is never measured from an arbitrary pivot/formation timestamp when that timestamp predates actual availability.

---

# 16. Approved baseline level types

The governed reference universe may contain:

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

Additional types require a versioned contract extension or a governed reference definition.

VWAP remains a separate optional anchored reference in v0.3.

---

# 17. Swing reference generation

The Set should generate and pass valid confirmed swing references on:

```text
15m
1h
```

whenever available.

The contract does **not** require all of:

```text
latest high
previous high
latest low
previous low
```

at both timeframes as universal completeness blockers.

Instead, every valid confirmed swing is added to:

```text
references.levels[]
```

with the corresponding `level_type`.

---

# 18. Optional swing convenience views

For Set-local audit and diagnostics, the matched-result record may include non-authoritative convenience views (not fields of the baseline wire payload):

```yaml
reference_views:
  swings:
    15m:
      latest_high_level_id:
      previous_high_level_id:
      latest_low_level_id:
      previous_low_level_id:

    1h:
      latest_high_level_id:
      previous_high_level_id:
      latest_low_level_id:
      previous_low_level_id:
```

These fields reference existing `level_id`s only.

They must never contain independent level prices.

`references.levels[]` remains the source of truth.

---

# 19. Previous-day levels

The Set should generate:

```text
PREVIOUS_DAY_HIGH
PREVIOUS_DAY_LOW
```

when available.

Canonical day boundary:

```text
UTC
```

These are approved reference types but are **not universally required** for handoff completeness.

They are inserted into `references.levels[]`.

---

# 20. Range references

When a governed range exists, its:

```text
RANGE_HIGH
RANGE_LOW
```

may be added to `references.levels[]`.

Range-specific descriptive context may also be persisted locally for audit; only the already-governed concrete levels enter the baseline wire payload:

```yaml
optional_context:
  range:
    range_id:
    timeframe:
    high_level_id:
    low_level_id:
    mid:
    width_price:
    width_pct:
    width_atr_15m:
    available_at:
    age_seconds:
    source_metric:
```

A range must never be invented ad hoc.

---

# 21. Direction-neutral relative-position classification

Each level may carry a cached classification relative to the frozen match price.

Canonical precedence:

```text
if abs(level.price - set_match_reference_price) <= tick_size:
    side = AT_REFERENCE

else if level.price < set_match_reference_price:
    side = DOWNSIDE

else:
    side = UPSIDE
```

`AT_REFERENCE` therefore has priority over `DOWNSIDE` / `UPSIDE` classification.

Schema:

```yaml
relative_position:
  side: DOWNSIDE | UPSIDE | AT_REFERENCE
  distance_price:
  distance_pct:
  distance_atr_15m:
```

---

# 22. Distance formulas

```text
distance_price =
abs(level.price - set_match_reference_price)
```

```text
distance_pct =
100 × distance_price / set_match_reference_price
```

```text
distance_atr_15m =
distance_price / ATR_15m
```

Cached distances must use:

```text
market_snapshot_at
set_match_reference_price
ATR_15m
```

from the same frozen handoff.

---

## Wire/calculation projection

Calculation notation `references.levels[]`, `ATR_15m`, `ATR_PCT_15m` and `relative_position.side` maps respectively to wire `reference_geometry.levels`, `volatility.atr_15m`, `volatility.atr_pct_15m` and each level's scalar `relative_position`. DOWNSIDE maps to BELOW_REFERENCE, UPSIDE to ABOVE_REFERENCE, and AT_REFERENCE remains AT_REFERENCE. The existing one-tick classification rule in this Part applies before serialization. Cached distances and capability predicates are derived from the same frozen price, tick size, ATR and level prices; no second identity, price source or live selection is introduced. Cache values may be retained locally but cannot be emitted as unknown wire properties.

# 23. Direction-aware interpretation belongs downstream

The Set does not permanently label references as SL or TP levels.

Dynamic SL/TP interprets reference side according to frozen direction.

## LONG

```text
DOWNSIDE
→ adverse-side geometry
→ SL candidate universe

UPSIDE
→ favorable-side geometry
→ TP candidate universe
```

## SHORT

```text
UPSIDE
→ adverse-side geometry
→ SL candidate universe

DOWNSIDE
→ favorable-side geometry
→ TP candidate universe
```

`AT_REFERENCE` levels are neither adverse-side nor favorable-side until downstream methodology explicitly handles them.

---

# 24. Universal handoff capabilities

Instead of requiring every reference family, the available frozen geometry determines the following capabilities. This is a Set-local diagnostic projection, not a second wire envelope. Position can validate the same availability predicates from the exact supplied primitives without querying markets, choosing a replacement thesis or changing direction. The canonical wire contract carries those primitives and resolved contexts; it does not carry a separate `handoff_capabilities` field.

Internal diagnostic shape:

```yaml
handoff_capabilities:
  reference_price:
    available:
    reason:

  tick_geometry:
    available:
    reason:

  volatility_scale:
    available:
    reason:

  downside_geometry:
    available:
    eligible_level_ids: []
    reason:

  upside_geometry:
    available:
    eligible_level_ids: []
    reason:

  dynamic_sl_base:
    available:
    reason:

  dynamic_tp_base:
    available:
    reason:
```

---

# 25. Capability rules

## `reference_price`

Available when:

```text
set_match_reference_price is AVAILABLE
```

## `tick_geometry`

Available when:

```text
tick_size is AVAILABLE and > 0
```

## `volatility_scale`

Available when:

```text
ATR_15m is AVAILABLE and > 0
ATR_PCT_15m is AVAILABLE
```

## `downside_geometry`

Available when at least one governed reference exists with:

```text
relative_position.side = DOWNSIDE
```

## `upside_geometry`

Available when at least one governed reference exists with:

```text
relative_position.side = UPSIDE
```

---

# 26. Baseline Dynamic SL capability

For LONG:

```text
dynamic_sl_base.available =
reference_price
AND
tick_geometry
AND
volatility_scale
AND
downside_geometry
```

For SHORT:

```text
dynamic_sl_base.available =
reference_price
AND
tick_geometry
AND
volatility_scale
AND
upside_geometry
```

This is only the universal base capability.

A specific Dynamic SL methodology/version may impose stricter requirements.

---

# 27. Baseline Dynamic TP capability

For LONG:

```text
dynamic_tp_base.available =
reference_price
AND
tick_geometry
AND
volatility_scale
AND
upside_geometry
```

For SHORT:

```text
dynamic_tp_base.available =
reference_price
AND
tick_geometry
AND
volatility_scale
AND
downside_geometry
```

Again, a specific TP methodology may require additional geometry later.

---

# 28. Important completeness distinction

A Set market handoff can be valid even when:

```text
dynamic_sl_base.available = false
```

or:

```text
dynamic_tp_base.available = false
```

The Set remains:

```text
matched = true
direction = LONG | SHORT
```

The capability predicate tells Position Rules whether the minimum common supplied geometry exists for that dynamic mode. It is derived from the frozen primitive inputs, not a second authoritative result message.

No Set direction is rewritten.

---

# 29. Capability reason codes

Recommended canonical reasons:

```text
AVAILABLE
MISSING_REFERENCE_PRICE
MISSING_TICK_SIZE
MISSING_VOLATILITY_SCALE
NO_DOWNSIDE_LEVEL
NO_UPSIDE_LEVEL
NO_GOVERNED_REFERENCE_LEVELS
```

A capability with:

```text
available = false
```

must carry a deterministic reason.

---

# 30. Optional VWAP

May be retained in the Set-local matched-result diagnostics; not a baseline wire field:

```yaml
optional_context:
  vwap:
    value:
    anchor_type:
    anchor_time:
    available_at:
    distance_price:
    distance_pct:
    distance_atr_15m:
```

Roles:

```text
BOTH_OPTIONAL
CONTEXT_ONLY
```

VWAP is not part of the canonical `references.levels[]` universe in v0.3.

---

# 31. Optional activity / liquidity

The Set-local matched-result diagnostics may include (not a baseline wire field):

```yaml
optional_context:
  activity:
    time_of_day_relative_turnover_5m:
    relative_turnover:
    trade_intensity:

  liquidity:
    turnover_liquidity:
```

Roles:

```text
CONTEXT_ONLY
TP_OPTIONAL
JOINT_FEASIBILITY
```

They are never universal Dynamic SL blockers.

---

# 32. Optional aggressive flow

The Set-local matched-result diagnostics may include (not a baseline wire field):

```yaml
optional_context:
  flow:
    aggressive_volume_delta_pct_5m:
    aggressive_volume_delta_pct_15m:
```

Roles:

```text
CONTEXT_ONLY
TP_OPTIONAL
```

No baseline Dynamic SL dependency is allowed.

---

# 33. Optional derivatives context

The Set-local matched-result diagnostics may include (not a baseline wire field):

```yaml
optional_context:
  derivatives:
    oi_change_pct_15m:
    oi_change_pct_1h:
    current_open_interest:
    funding_rate:
    premium_index:
    mark_index_spread_pct:
```

Roles:

```text
CONTEXT_ONLY
TP_OPTIONAL
JOINT_FEASIBILITY
```

No required baseline dependency.

---

# 34. Optional benchmark / cross-sectional context

The Set-local matched-result diagnostics may include (not a baseline wire field):

```yaml
optional_context:
  benchmark_context:
    btc_context_score:
    btc_structure_state_1h:
    btc_return_15m:
    relative_return_vs_btc_15m:

  cross_sectional_context:
    market_breadth:
    momentum_rank:
    relative_volatility:
    dispersion:
```

Roles:

```text
CONTEXT_ONLY
TP_OPTIONAL
```

Direction is already frozen.

These fields may never reverse direction downstream.

---

# 35. Optional session context

The Set-local matched-result diagnostics may include (not a baseline wire field):

```yaml
optional_context:
  session:
    session_id:
    time_of_day_bucket:
    minutes_since_session_start:
    minutes_to_session_boundary:
    current_session_high:
    current_session_low:
    previous_session_high:
    previous_session_low:
```

Roles:

```text
CONTEXT_ONLY
TP_OPTIONAL
```

Session levels may only become formula inputs after session definitions are governed.

---

# 36. Optional exchange reference context

The Set-local matched-result diagnostics may include (not a baseline wire field):

```yaml
optional_context:
  exchange_reference:
    mark_price:
    index_price:
```

Roles:

```text
CONTEXT_ONLY
SL_OPTIONAL
JOINT_FEASIBILITY
```

These are not structural invalidation levels.

---

# 37. Explicitly excluded from Set market geometry

Do not place the following under Set-owned market geometry:

```text
planned_entry_reference
actual_fill_price

position_size
quantity
leverage

requested_notional
available_notional
allocation_gap
remaining_slots

spread_pct
estimated_round_trip_cost

min_order_qty
qty_step
min_notional

existing_position
average_entry
existing_stop
unrealized_pnl
position_age
```

---


## Set / Position Rules ownership boundary

### Set owns

- market match;
- direction;
- market snapshot;
- market reference geometry;
- volatility and approved market context;
- `entry_context`;
- `sl_context`;
- `tp_context`;
- frozen Market Invalidation Inputs;
- `decision_cycle_id` creation;
- pending-order market-validity analysis.

### Position Rules owns

- final Entry;
- final Stop Loss;
- final Take Profit;
- leverage;
- quantity;
- target order notional;
- fees/economics;
- risk/reward and net-edge gates;
- `APPROVE / REJECT`;
- final Order Spec.

### Order Lifecycle owns

- order submission;
- exchange acknowledgement;
- fills;
- cancellation execution;
- reconciliation;
- close processing;
- order lifecycle state.

Set never changes final trade parameters after Position Rules has created them.

---

# 39. Dynamic SL consumer contract

Dynamic SL receives:

```text
immutable Set Market Handoff
+
planned_entry_reference
+
active Position Rules SL configuration
```

It may use:

```text
references.levels[]
ATR_15m
ATR_PCT_15m
optional approved context
```

according to the Dynamic SL methodology version.

It may not request Set to rewrite historical direction.

---

# 40. Dynamic TP consumer contract

Dynamic TP receives:

```text
immutable Set Market Handoff
+
planned_entry_reference
+
active Position Rules TP configuration
```

It may use optional context only where explicitly approved by the TP methodology.

---

# 41. Joint TP/SL feasibility

Joint feasibility receives:

```text
planned_entry_reference
SL candidate
TP candidate(s)
immutable Market Handoff
Position Rules constraints
execution/cost inputs where relevant
```

It may assess:

```text
risk distance
reward distance
reward/risk
target reachability
stop width
tick legality
net economics
```

It must not redefine frozen direction.

---

# 42. No circular recalculation

Prohibited:

```text
Position Rules
→ Set re-analysis
→ changed historical direction
→ recompute original handoff
```

Canonical:

```text
Set match
→ frozen handoff
→ downstream calculations
```

Future active-position refreshes belong to a separate Dynamic Position Management methodology.

---

# 43. Canonical Market Handoff wire schema

The business contract wire schema is canonical. The richer internal Set record must serialize one-to-one into it; it is not a second incompatible canonical payload.

```yaml
market_handoff:
  contract_version: 4
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  created_at: RFC3339-timestamp
  set_provenance:
    set_id: string
    set_version: string
    core_set_id: string
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
  snapshot:
    matched_at: RFC3339-timestamp
    market_snapshot_at: RFC3339-timestamp
    market_snapshot_id: string
    direction: LONG | SHORT
    set_match_reference_price: decimal-string
    reference_price_basis: LAST_TRADED_PRICE
    reference_price_observed_at: RFC3339-timestamp
    reference_price_source: string
  instrument:
    tick_size: decimal-string
    metadata_revision: string
    metadata_as_of: RFC3339-timestamp
  volatility:
    atr_15m: decimal-string
    atr_pct_15m: decimal-string
  reference_geometry:
    levels:
    - level_id: string
      level_type: string
      price: decimal-string
      timeframe: string
      formed_at:
        nullable: RFC3339-timestamp
      confirmed_at:
        nullable: RFC3339-timestamp
      available_at: RFC3339-timestamp
      source_metric:
        nullable: string
      age_seconds: nonnegative-integer
      relative_position: BELOW_REFERENCE | AT_REFERENCE | ABOVE_REFERENCE
  entry_context:
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_id:
      nullable: string
    origin_binding:
      nullable:
        binding_id: string
        role_id: string
        core_set_id: string
        core_set_constituent_id: string
        trigger_id: string
        trigger_version: string
        trigger_occurrence_id: string
        reference_key: string
        indicator_id:
          nullable: string
        timeframe: string
        level_id: string
  sl_context:
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_id:
      nullable: string
    origin_binding:
      nullable:
        binding_id: string
        role_id: string
        core_set_id: string
        core_set_constituent_id: string
        trigger_id: string
        trigger_version: string
        trigger_occurrence_id: string
        reference_key: string
        indicator_id:
          nullable: string
        timeframe: string
        level_id: string
  tp_context:
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_id:
      nullable: string
    origin_binding:
      nullable:
        binding_id: string
        role_id: string
        core_set_id: string
        core_set_constituent_id: string
        trigger_id: string
        trigger_version: string
        trigger_occurrence_id: string
        reference_key: string
        indicator_id:
          nullable: string
        timeframe: string
        level_id: string
  set_numeric_policy_version: TT_SET_NUMERIC_V1
```

## 43.1 Context production rules

P4 governs every context. All role/indicator/timeframe/reference identities are inherited from the exact Trigger/Set configuration and concrete MATCHED Core Set, not selected afterward. Set persists configured constituent/reference → exact concrete level_id for the matched Trigger occurrence. Position only consumes/validates the result.

Versioned producer configuration:

```yaml
position_context_policy:
  set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
  role_bindings:
    - role_id:
      core_set_constituent_id:
      trigger_id:
      trigger_version:
      reference_key:
      indicator_id: null
      timeframe:
  entry:
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_role: null
  sl:
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_role: null
  tp:
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_role: null
```

role_id is a nonempty unique string scoped to the Set version. Each non-null thesis_reference_level_role references exactly one role_bindings entry. core_set_constituent_id identifies the configured Trigger slot; reference_key identifies its concrete produced reference. At MATCHED the persisted trigger_occurrence_id and reference mapping provide the exact level_id; Set persists binding_id and serializes origin_binding into the appropriate context. A configured indicator_id may be null only for a structural/non-indicator reference; timeframe must still match. Multiple same-type levels do not create ambiguity when the exact constituent reference is known.

REQUIRED must resolve uniquely to an available frozen level or makes the handoff UNAVAILABLE with no emission. PREFERRED uses the exact binding or genuine absence/null under existing Dynamic fallback semantics; a conflicting/nonunique binding is an error, not a choice. NONE has null role, thesis ID and origin binding. Missing required configuration never causes downstream inference.

No latest/closest/strongest/nearest post-MATCH thesis heuristic exists. The existing Position PREFERRED/NONE default calculation hierarchies are not producer role resolution and do not rewrite the bound thesis reference. Frozen Condition remains in Set; none of these context fields transmits it.

---

# 44. Missing-data semantics

Set classifies internal analysis facts as AVAILABLE, UNAVAILABLE or NOT_APPLICABLE. An unavailable fact is neither numeric zero nor false. These are internal analysis statuses, not replacement values for required fields of the strict MARKET_HANDOFF payload.

Before emission the mandatory identity, snapshot, direction, reference price, tick size, volatility and all three policy contexts must be populated under the canonical contract. REQUIRED thesis bindings must resolve uniquely. If a required value is unavailable, Set persists the unavailability reason and emits no valid downstream handoff.

`reference_geometry.levels` is the wire array. The calculation notation `references.levels[]` used in this methodology names that same array; it never identifies a second source. The array may be empty only when the configured contexts and unchanged Position calculation dependencies permit it. In particular, an empty array never satisfies REQUIRED. Availability/capability diagnostics remain deterministic views of these supplied primitives; absence of geometry cannot be replaced with an invented level.

Optional research/diagnostic contexts in this Part are not mandatory baseline wire dependencies. They remain Set-local records unless incorporated by an explicit versioned wire extension; they cannot be emitted as unknown fields or silently used by a current Position formula.

---

# 45. Audit requirements

The handoff must allow reconstruction of:

```text
exact market snapshot
direction
reference price
volatility scale
all governed reference levels
when each reference became available
where each level sat relative to frozen price
which geometry capabilities existed
why any capability was unavailable
```

Downstream logic may not invent hidden levels.

---

# Part IV — Pending Order Market Validity

This Part absorbs the previously separate Pending LIMIT Market Validity work into the Set methodology.

There is **no separate Pending Entry Validity Monitor architecture block**.

Canonical runtime:

```text
Set MATCHED
→ decision_cycle_id created
→ frozen Market Invalidation Inputs retained inside Set
→ Market Handoff sent to Position Rules
→ Position Rules initial APPROVE (no capital_grant_id)
→ Portfolio issues Capital and Limits for that approved cycle/decision
→ Position completes post-grant construction
→ Position durably publishes Order Spec to Lifecycle and CONSTRUCTED confirmation to Portfolio
→ Portfolio atomically books SUBMISSION_HOLD and emits Submit Authorized
→ Lifecycle receives the matching immutable spec and authorization, then submits
→ order accepted / placed
→ Order Lifecycle sends Order Placed + decision_cycle_id to Set
→ Set activates the matching frozen invalidation state
```

While valid:

```text
Set sends nothing
```

When invalid:

```text
Set → Order Cancel Signal
→ Order Lifecycle
```

Set evaluates market validity.
Order Lifecycle executes order management.

The following validity rules preserve the substantive conclusions of the prior expert-council review while placing the responsibility inside Set.

# 12. Canonical frozen market-invalidation shape

Each Set version that can create a pending LIMIT entry must define its own versioned frozen market-invalidation conditions.

Canonical structure:

```yaml
market_invalidation:
  version: string
  condition_record_id: string
  decision_cycle_id: string
  set_result_id: string
  set_version: string
  set_family: string
  direction: LONG | SHORT
  created_at: RFC3339-timestamp
  source_market_snapshot_at: RFC3339-timestamp
  configuration_id: string
  configuration_version: string
  configuration_content_digest: string
  hard_conditions:
    - condition_id: string
      metric_or_reference: typed-identifier
      operator: LT | LTE | GT | GTE | EQ | NEQ | CROSSED_BELOW | CROSSED_ABOVE | BROKEN | CONTRADICTED
      threshold_or_reference: typed-threshold-or-reference
      timeframe_or_horizon: typed-timeframe-or-horizon
      freshness: typed-freshness-rule
      unavailable_policy: FAIL_SAFE_CANCEL
      evidence_selector: typed-selector
```

Important:

The Set must store **deterministic conditions**, not a prose explanation.

These conditions are frozen at the original Set match and are activated only after the matching `Order Placed` event arrives.

hard_conditions must contain at least one valid condition. Empty,
missing, malformed or unsupported condition sets cannot evaluate VALID. The
record is created/persisted with the original matched cycle and is identified
by condition_record_id; set_result.frozen_condition_record_id points to that
same record. Retain its digest and configuration_id, configuration_version and
configuration_content_digest. The Set/Trigger/Core Set configuration selected
for the formation epoch remains pinned for this matched cycle; later edits
apply only to later cycles.

Each metric/reference, operator, threshold/reference, timeframe/horizon,
freshness rule and evidence_selector must have a deterministic typed meaning
in the frozen Set configuration. No concrete condition list, metric-specific
operator meaning or new threshold is selected here. Missing/malformed fields
or unsupported operator/reference yield INVALID_CONDITION with the §12A
unavailable/fail-closed handling. unavailable_policy is FAIL_SAFE_CANCEL, not
an implementer-selected policy.

---

# 12A. Canonical pending-validity reducer — F-013

F-013 governs already-placed pending LIMIT **entry remainder only**. It
requires a matched cycle and its persisted frozen record followed by actual
Order Placed acceptance/placement. It does not govern unmatched evaluations,
submission attempts without exchange acceptance, definitive no-create
failures, market orders or filled exposure after entry remainder is gone.

### Activation identity

Monitoring activates only after actual exchange acceptance/placement when:

```text
Order Placed.decision_cycle_id == frozen_condition.decision_cycle_id
AND
Order Placed.set_result_id == frozen_condition.set_result_id
AND
Order Placed.tranche_id is linked to that matched cycle
```

Set must not activate monitoring by symbol, order timestamp, nearest order,
latest Set result or current configuration. Ambiguous activation identity fails
closed and records an integrity/reconciliation condition; Set does not guess an
order.

### Per-condition evaluation

Each hard condition evaluates to:

```text
TRUE
FALSE
UNAVAILABLE
INVALID_CONDITION
```

Evaluation uses only the frozen predicate definition and the current factual
measurements explicitly selected by that frozen definition. It never updates the
original threshold, reference identity, configuration binding or condition list.

For Set-derived numeric dependencies, use `TT_SET_NUMERIC_V1`, exact comparisons
with no epsilon and eligible factual evidence only.

TRUE means that the frozen **invalidation** condition holds, not that the
pending order remains valid.

Current full-Set mismatch is not itself an invalidator. Cancellation on this
basis is permitted only when an already-frozen hard condition independently
evaluates TRUE according to its certified semantics; a full-Set rematch is not
required.

Existence of a newer opportunity is not an F-013 invalidator and cannot be made
one merely by freezing a newer-opportunity predicate.

Arbitrary order age is not an F-013 invalidator and cannot become a timer-based
TTL. This does not prohibit genuine frozen-condition evidence freshness or
horizon semantics intrinsic to the certified condition itself. Unavailable
required evidence follows the UNAVAILABLE branch, not a fabricated TRUE
age-based predicate.

Coins CLOSE stops only new formation; it does not stop this existing
matched-cycle monitor.

### Canonical outcome precedence

For an active monitor, reduce evidence to exactly one outcome:

```text
1. If authoritative Order Lifecycle evidence proves no active unfilled entry
   remainder remains:
   pending_validity = STOPPED
   action = NO_MARKET_SIGNAL

2. Else if activation identity or frozen condition record is invalid,
   unresolved or unsupported:
   pending_validity = UNAVAILABLE
   action = FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING

3. Else if any frozen hard condition evaluates TRUE:
   pending_validity = INVALID
   action = EMIT_ORDER_CANCEL_SIGNAL

4. Else if any required hard condition evaluates UNAVAILABLE or
   INVALID_CONDITION:
   pending_validity = UNAVAILABLE
   action = FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING

5. Else all valid required hard conditions evaluate FALSE:
   pending_validity = VALID
   action = NO_MESSAGE
```

Known TRUE hard invalidation takes precedence over unavailable evidence for
another condition. Authoritative terminal remainder state takes precedence over
market evaluation.

### Signal and unavailable handling

When INVALID, emit the version-2 Order Cancel Signal with cause INVALIDATION
as defined in Part I §4.2, with condition_record_id, condition_id and evidence_digest. invalidated_at is
the authoritative effective time of the evidence making the predicate TRUE.
Repeated evaluation of the same frozen condition, evidence digest and active
remainder retains the same logical signal / original signal_id on replay.

When `UNAVAILABLE`, Set records the unavailable state and requests fail-closed
handling:

```text
Set marks MONITORING_UNAVAILABLE
→ reconcile order state first
→ if Lifecycle proves no active unfilled remainder:
     STOPPED, no market cancel signal
→ if still pending:
     emit or preserve cancel-required signal/intention for the unfilled
     remainder
```

Market recovery must not silently erase an already required unavailable
cancellation for the same active remainder.

The UNAVAILABLE branch uses `ORDER_CANCEL_SIGNAL` cause
`MONITORING_UNAVAILABLE` from Part I §4.2. It does not invent a TRUE predicate,
condition ID, evidence digest or effective invalidation time. Its common
cycle/result/tranche/symbol fields must identify the original accepted entry
through retained explicit lineage independently of a usable frozen record.
The canonical contract Semantics defines the following required mapping.

**Establishment and identity.** Set durably records the first
MONITORING_UNAVAILABLE transition and its original effective timestamp before
publication. For an exactly bound accepted entry, atomically acquire-or-join
one sticky `unavailable_requirement_id` under the semantic key
`(F013_MONITORING_UNAVAILABLE, decision_cycle_id, set_result_id, tranche_id,
original entry client_order_link_id)`, within that entry's existing
account/environment lineage. The accepted client/native entry pair is retained
from actual Order Placed and Lifecycle state, never inferred from symbol/time.
`signal_id` is the same identity as `unavailable_requirement_id`. Partial fills,
remainder quantities/revisions, retry count, fresh market observations,
additional unavailable conditions and recovery do not change this key or mint
another requirement. Concrete opaque-ID encoding remains an implementation
detail under IDENTIFIER_LINEAGE; the durable key-to-identity mapping is unique
and replay-stable.

**Truthful effective time and reason.** `unavailable_at` is the once-persisted
effective timestamp of the first durable MONITORING_UNAVAILABLE transition
establishing the requirement. It is not a guessed missing-evidence timestamp,
TRUE invalidation time, delivery time or a refreshed retry clock. A deferred
exact-target binding retains that original transition time. Select
`unavailable_reason_code` only after the unchanged reducer returns UNAVAILABLE.
At first establishment, the deterministic reporting order is
ACTIVATION_IDENTITY_INVALID, FROZEN_RECORD_INVALID_OR_UNRESOLVED,
INVALID_CONDITION, REQUIRED_EVIDENCE_UNAVAILABLE. Retain all independently
known failures locally; freeze the primary reason. This order distinguishes
failure classes without changing the certified reducer or its TRUE/terminal
precedence. Later facts do not rewrite the requirement reason or timestamp.

**Reconcile-first delivery.** Set records the requirement and its outgoing
content atomically before it can be published. If the current authoritative
terminal tombstone is already known, return STOPPED and publish no new request.
Otherwise this same-cause envelope carries the fail-closed request to Lifecycle
for reconciliation. Before positive pending proof it is only a conditional
request, not a TRUE market-cancel signal or native cancellation authority.
Lifecycle reconciles first: terminal/no remainder makes the request no longer
applicable without cancellation; proven active remainder admits/preserves the
sticky cancel-required intention; unavailable remainder proof retains the
request for reconciliation without guessing or dropping it. No second
message family, shared-state shortcut, Set → API order call or new edge is
needed. Order Placed/entry-lifecycle events remain the return boundary.

**Invalid activation or record.** A missing/corrupt/unresolved frozen record
cannot force synthetic condition fields. A trusted original matched record ID
may be included only as the optional record reference; otherwise omit it. If
actual placement and exact routing lineage are already authoritative but the
activation-to-record binding is invalid, send the same-cause request with
ACTIVATION_IDENTITY_INVALID. If even the target cycle/result/tranche/entry
cannot be uniquely established, retain the original unavailable transition
and integrity/reconciliation condition under its existing exact source/event
identity; publish no guessed-target envelope. Only independent authoritative
lineage resolving that same incident can attach it to the original accepted
entry and acquire-or-join its requirement. Resolution cannot select another
opportunity or erase the original fail-closed obligation. Terminal proof
instead ends applicability. Missing local authority is not a fabricated order.

**Sticky applicability.** Market recovery cannot retract, clear, reclassify or
remint an established requirement. A later evaluation's VALID/NO_MESSAGE does
not revoke the earlier durable cancellation obligation or its retries; the
reducer itself is unchanged. Any independently required INVALIDATION signal
retains its own cause/evidence. Lifecycle joins requests for the same entry to
its existing cancel intent; neither cause authorizes a second entry or a
filled-exposure close. Only authoritative terminal remainder proof ends this
requirement's applicability.

### Stop, persistence and replay

Monitoring stops only when Order Lifecycle authoritatively confirms no active
unfilled entry remainder remains because the entry is fully filled, cancelled,
rejected, submission failed or otherwise terminal.

F-013 never closes already filled exposure.

An emitted cancellation does not itself prove terminal remainder state;
monitoring remains logically pending until authoritative Lifecycle confirms
the terminal cancel/fill outcome. Evaluation is event/condition-driven from
relevant completed bars, level/required-market-data events, stream health or
reconnect/recovery, without inventing a timeout or age rule.

F-013 persists condition record and digest, activation identity, monitor state,
last evidence identity/digest, emitted cancel signal identity,
unavailable/fail-closed requirement and Lifecycle terminal/tombstone revisions.

Restart restores these facts. It must not rebuild a condition from current
configuration, latest Set result, current snapshot, nearest order or current
market data.

Persist the unavailable cancellation requirement until authoritative terminal
remainder proof; market recovery cannot erase it. Restore its semantic key,
unavailable_requirement_id, identical signal_id, immutable cause/content,
unavailable_at, initial reason, optional-record presence/value, original
transition/activation/entry binding, outbox publication/delivery state and
current authoritative Lifecycle remainder revision/tombstone. Identical
replays return the committed identity/content; a changed payload under the
same identity is an integrity/reconciliation condition, not an update. An
acknowledgement alone never proves cancellation. A terminal tombstone retains
the requirement's deduplication binding and prevents replay/restart from
reactivating it. Missing or conflicting recovery state is not zero/no
requirement and must not be repaired by reminting. Filled quantity remains
real exposure under its established TP/SL/Manual Close and S-004 finality rules.
There is no KEEP signal, full-Set rematch requirement, reprice, chase or
Portfolio capital-release authority in F-013.

---

# 13. What kinds of conditions may be valid?

The council recommends three categories.

## 13.1 Thesis invalidation

Example:

```text
original LONG setup required support X
support X is decisively broken
→ INVALID
```

## 13.2 Direction/context contradiction

If a condition that was essential to the Set match becomes explicitly contradicted.

Important:
Do not require the entire Set to match continuously.

Otherwise a minor trigger flicker may cancel too aggressively.

Use only designated hard-validity conditions.

## 13.3 Entry-context invalidation

Example:

```text
planned entry was a pullback to a structural zone
market moved through / away in a way that destroys that setup
```

This must be defined by Set context, not improvised by Order Lifecycle.

---

# 14. What should NOT automatically invalidate a pending order?

Council recommendation:

Do not cancel merely because:
- cooldown expired;
- a newer Set opportunity exists;
- price moved slightly;
- one non-critical metric changed;
- current Set no longer fully matches;
- order age exceeded an arbitrary short timer.

Only explicit hard validity conditions should cancel.

---

# 15. Fresh formation versus pending-order monitoring

These are independent Set scopes.

For every existing accepted pending order:

```text
its decision_cycle_id keeps its own frozen invalidation monitor
until that entry lifecycle becomes terminal
```

Separately, while Portfolio `Coins` state for the symbol is OPEN, Set may run a new formation cycle whenever the approved Set re-arm rule permits it, even if an older independent cycle still has a pending order and its own monitor.

Canonical:

```text
pending cycle A
→ monitor only A frozen conditions

Coins OPEN + re-arm permits a fresh formation
→ independent cycle B may be created
→ B gets a new decision_cycle_id
```

If cycle A is invalidated, its cancellation/reanalysis sequence applies only to replacement of A. It must not cancel, overwrite, or prevent an otherwise eligible independent cycle B.

`Coins CLOSE` stops new formations only; it does not stop an already active monitor.

---

# 16. Validation frequency

Do not use an arbitrary fixed polling timer as the semantic rule.

Preferred triggers:

```text
new relevant completed bar
reference-level event
market-data event required by the contract
data-stream health change
system reconnect/recovery
```

The implementation may have operational timers, but market validity is event/condition-driven.

---

# 17. Outage behavior

If the validator loses reliable market data:

```text
validity = UNAVAILABLE
```

For pending unfilled LIMIT entry, apply the reconcile-first fail-safe:

```text
Set records MONITORING_UNAVAILABLE
→ request fail-closed handling and reconcile order state first
→ if Lifecycle proves no active unfilled entry remainder:
     STOPPED; no market cancel signal
→ if an unfilled remainder is still pending:
     emit or preserve cancel-required signal/intention for that remainder
```

Loss of market evidence is not proof of an active or terminal native order.
An unresolved activation/remainder identity is surfaced for reconciliation;
Set must not guess a target order or invent TRUE-condition evidence.

If the order filled during the outage:
- do not pretend it is still pending;
- treat actual filled exposure as a real tranche;
- exchange-side TP/SL remain authoritative.

If still pending:
- retain and execute the required cancellation of only the unfilled remainder
  through Order Lifecycle;
- recovery of market data must not erase an already required cancellation;
- retain the frozen condition/evidence/activation and original signal identity
  across restart until authoritative terminal remainder proof.

The four-outcome reducer and precedence in §12A apply. Its governed
`MONITORING_UNAVAILABLE` cause carries the original unavailable_requirement_id,
unavailable_at and unavailable_reason_code; it does not populate the TRUE
invalidation fields. Exact unresolved-target handling, conditional request
delivery, receipt and restart use §12A and Order Cancel Signal Semantics.
F-013 never closes filled exposure; physical flatness or a cancel intention does not replace the
canonical S-004 CLOSED predicate or authorize Portfolio release.

---

# 18. Zero-fill invalidation flow

Canonical:

```text
Set pending-order monitoring → INVALID
↓
Set → Order Cancel Signal
↓
Order Lifecycle → cancel request
↓
exchange confirms zero-fill cancel
↓
Order Lifecycle → Order Event
↓
Portfolio Rules
→ Portfolio Data Request
→ API
→ recompute current portfolio state
→ update Coins OPEN / CLOSE as required
```

---

# 19. Partial-fill invalidation flow

If order is already partially filled when the pending context becomes invalid:

```text
cancel remaining unfilled entry immediately
```

The filled portion remains a real logical tranche.

Do not automatically close the filled portion merely because the unfilled entry context became invalid.

Reason:
- it already has its own TP/SL and is now an existing position;
- close policy remains TP / SL / Manual Close only.

Thus:

```text
INVALID pending context
→ cancel remainder
→ keep filled exposure
```

This is consistent with current product rules.

---

# 20. Filled portion later closes

If the partially filled tranche later closes by:
- TP;
- SL;
- Manual Close;

any remaining entry quantity must already have been cancelled.

No closed tranche may retain a live entry remainder capable of reopening exposure.

---

# 21. Auto-reprice

**Decision:** `DISABLED`

Invalid pending entry is never repaired by:
- moving limit price;
- trailing;
- chasing;
- replace-with-new-price.

Canonical:

```text
INVALID
→ CANCEL OLD
→ Portfolio Rules
→ NEW SET CYCLE
→ NEW Position Rules decision
→ NEW order if valid
```

---

# Part V — Canonical Runtime Invariants

1. `Coins OPEN / CLOSE` is controlled by Portfolio Rules.
2. `OPEN` means Set may analyze that symbol for a new opportunity.
3. `CLOSE` means Set stops **new-opportunity analysis** for that symbol.
4. `CLOSE` does not terminate monitoring of an already placed pending order.
5. Set never independently adds or removes symbols from active analysis scope.
6. A `decision_cycle_id` is created by Set only when a valid Set is `MATCHED` and handed downstream.
7. `decision_cycle_id` is propagated unchanged through Position Rules and Order Lifecycle and returned in `Order Placed`.
8. `Set = NONE / not matched / unavailable` creates no trade-decision cycle.
9. Every new matched opportunity receives a fresh `decision_cycle_id`; old Set Results are never reused.
10. Direction is Set-owned and immutable downstream.
11. Position Rules must not re-infer or reverse direction.
12. Market Handoff is frozen at the original Set match.
13. Market Invalidation Inputs remain inside Set.
14. Pending-order monitoring starts only after `Order Placed`.
15. Set monitors only the frozen hard invalidation conditions associated with that specific decision cycle.
16. The entire Set is not required to remain continuously matched while a LIMIT order is pending.
17. No minor trigger flicker, small price movement, cooldown expiry, newer opportunity, or arbitrary short age automatically invalidates an order.
18. No auto-reprice, chase, or market fallback is implied by Set invalidation.
19. `INVALID` causes `Order Cancel Signal`; Set does not cancel the order itself.
20. For partial fill, invalidation cancels only the unfilled remainder; already filled exposure remains governed by its existing TP / SL / Manual Close logic.
21. Missing required market data must remain distinguishable as `UNAVAILABLE`.
22. No look-ahead is allowed.
23. Backtest, paper, demo, and live implementations must use the same versioned semantics for the same Set version.
24. Set logic must be auditable from inputs to match, direction, handoff, frozen invalidation state, and any cancel signal.

---

# Part VI — Source Consolidation Map

The following prior documents are source specifications for this consolidated methodology:

```text
TRIGGERTRADE_SET_CONTRACT_v0.7.2_COIN_OPEN_CLOSE_SCOPE_DRAFT
→ consolidated into Part I and Part V

TRIGGERTRADE_DIRECTION_CLASSIFIER_v0.4.1_APPROVED_RESEARCH_CANDIDATE
→ consolidated into Part II

TRIGGERTRADE_DYNAMIC_POSITION_INPUTS_SET_HANDOFF_CONTRACT_v0.3.1_APPROVED
→ consolidated into Part III

Entry / SL / TP Set Handoff amendments
→ semantically retained as governed Market Handoff contexts

TRIGGERTRADE_PENDING_LIMIT_MARKET_VALIDITY_EXPERT_COUNCIL_REVIEW_v0.1
→ substantive conclusions consolidated into Part IV;
  obsolete separate-monitor architecture is superseded
```

After approval of `SET.md`, these source documents remain historical evidence/review artifacts rather than parallel canonical Set methodologies.

---

# Appendix A — Ordered scope and monitor synchronization (v1.1.0)

## Coins scope ordering

Each Portfolio → Set symbol update carries a Portfolio-owned monotonically increasing `scope_revision`. Set applies an OPEN/CLOSE update only when its revision is newer than the last applied revision for that symbol. Omitted symbols are unchanged; the contract is delta-based unless an explicit future snapshot mode says otherwise.

## Pending monitor ordering

Each Order Lifecycle → Set placement/terminal message carries a monotonically increasing `lifecycle_revision` for its `decision_cycle_id`. Set persists a terminal tombstone when the entry phase becomes terminal. Terminal state dominates activation:

```text
terminal event first
then delayed ORDER_PLACED
→ monitor remains STOPPED
```

A terminal cycle is never reused for a future formation.

# Appendix D — Decision-cycle Frozen Condition binding

For each concrete MATCHED cycle, Set creates decision_cycle_id/set_result_id, persists the Core Set's constituent/Trigger-occurrence reference mappings, exact context origin_bindings and Frozen Condition. Only the Market Handoff shape goes to Position; the condition itself never does. P4 defines the exact producer relation; no type-based or latest/nearest heuristic fills a missing role.

Order Placed.decision_cycle_id selects this exact persisted Frozen Condition. Concurrent cycles remain independent; a later match cannot replace an earlier pending monitor. Entry-terminal revisions persist a tombstone and prevent delayed placement from reactivating the cycle after restart. Set receives no capital/grant and is never asked to rerun analysis to repair a failed construction or hold.

---

## Deterministic numeric and historical-source representation

`../schemas/SET_NUMERIC_POLICY.md` is normative for all existing Set-derived arithmetic: exact raw decimals/ordering, named-output 36-fractional-decimal HALF_EVEN working values, canonical Wilder seed/recurrence/checkpoint ancestry, exact population variance and integer-midpoint sqrt, and 18-fractional-decimal Market Handoff values. Existing formulas, timeframes, trigger logic, normalization windows, thresholds and exact bound references are unchanged. Market Handoff v4 declares `set_numeric_policy_version = TT_SET_NUMERIC_V1`; Position consumes its canonical ATR values without independent recomputation. Frozen matched references/conditions remain Set-owned and immutable.

For new analysis and pending-cycle monitoring, Set fixes and persists analytical as_of and each factual dataset selector before Market Data Request v3 dispatch. Requests explicitly select historical [range_from, range_to) and closed-candle timeframe/count where applicable; current/as-of point facts use AS_OF mode. Set owns analytical window selection: ordinary normalization selects the fixed-UTC completed-calendar-day population in Part II §6, while explicitly governed metric-specific selectors retain their own rules. Set expresses the selected exact boundaries as UTC `Z` timestamps; API serialization does not choose the analytical calendar or infer windows or market logic. A recovered cycle reuses its selection identity/cutoff and checkpoint. Missing ranges, source gaps, conflicting source identities or incomplete page manifests retain PARTIAL/UNAVAILABLE and cannot be replaced with a current snapshot or shifted baseline. See SYSTEM_PROTOCOLS P16 and the API contract for complete page/coverage semantics.

## Historical evidence eligibility

Historical selector ownership and TT_SET_NUMERIC_V1 are unchanged. Under SYSTEM_PROTOCOLS S04, assembled input is eligible only while its exact request/selection/snapshot/page/source-completeness proof remains consistent. New relevant page evidence invalidates current derived eligibility pending deterministic assembly; incompatible complete manifests or immutable source-record content put the affected selection into integrity reconciliation. Persist that state across restart. Preserve already frozen Market Handoff bytes/evidence for audit and replay; never silently rewrite them or treat a contradicted assembly cache as eligible input to a new decision cycle.


## T05 — Working normalization versus diagnostic serialization

TT_SET_NUMERIC_V1 and all configured formula/threshold/window semantics are
unchanged. The Set-owned working-normalization operation, denoted
normalize_working (also normalize), returns the canonical 36-fractional-place
working result. Set gates compare this
value before any 18-place diagnostic/export serialization. The separate Set-owned
serialization operation, denoted serialize_normalized_for_handoff, is used only
at an already-governed boundary; it adds no new Market Handoff field and never changes working state.
Persist/restore working values and source/checkpoint proof, not exports, for gate
replay. No epsilon, binary float, new veto or threshold is introduced. For 8,640
alternating −1/+1 samples and value −1.9999999999999999999, mean=0 and population
stddev=1; the existing LONG veto VNM_5m_z <= −2 is false. A later diagnostic value
−2 is not a permitted replacement for that gate input.


## V05 historical evidence eligibility

SYSTEM_PROTOCOLS.md V05 governs response ingestion for the existing historical selection. A semantically rejected payload challenging an accepted page/source identity must durably invalidate current assembly eligibility, not leave AVAILABLE after rollback. The original page evidence and already frozen Market Handoffs remain immutable; new analysis/handoff generation is blocked until existing authoritative reconciliation requirements are met. Unrelated malformed requests/selections do not poison accepted evidence. Numeric formulas, Set logic, triggers, direction, Core Set, Frozen Condition and market selectors are unchanged.
