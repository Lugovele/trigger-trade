# F-013 Revised Specification - Cycle 1

# F-013 - Set Pending Invalidation and Stale-Signal Eligibility

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-013 |
| Formula name | Set pending invalidation and stale-signal eligibility |
| Owner | Set |
| Formula family | SYSTEM_FORMULA |
| Candidate | `F-013_REVISED_SPEC_CYCLE_1` |
| Active methodology baseline | v1.2.14 |
| Source Pack | `docs/formula-certification/F-013/F-013_SOURCE_PACK.md` |
| Revision basis | Full Council Review Cycle 1 blockers B1-B5 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = PENDING_REVIEW
ANOTHER_REVIEW_CYCLE_REQUIRED = YES
```

## 3. Intended Purpose

F-013 defines the deterministic Set-owned state predicate for an already placed
pending LIMIT entry:

```text
Does the original frozen Set market-validity condition remain valid, become
invalid, become unavailable, or stop because no active unfilled entry remainder
exists?
```

Its trading role is to avoid leaving stale pending entry orders live after the
original hard market thesis is invalidated, while preventing over-aggressive
cancellation from minor signal flicker, newer opportunities, ordinary loss of a
full Set match, cooldown expiry or arbitrary order age.

## 4. Actual Construct

F-013 is a state predicate over:

- a matched Set cycle with persisted frozen Market Invalidation Inputs;
- the actual `Order Placed` activation identity returned by Order Lifecycle;
- current eligible factual evidence required by the frozen hard conditions;
- authoritative Order Lifecycle state for the active unfilled entry remainder.

F-013 is not a new indicator and has no universal standalone numeric threshold.
The generic F-013 framework requires valid, nonempty versioned hard conditions
for any Set version that can create a pending LIMIT entry. Certification of this
framework does not certify every future concrete condition set, threshold or
research parameter.

## 5. Exact Rule

### 5.1 Required frozen condition record

For each matched Set cycle capable of producing a pending LIMIT entry, Set must
persist a frozen condition record:

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

`hard_conditions` must contain at least one valid condition. Empty, missing,
malformed or unsupported hard-condition sets are invalid frozen condition
records and cannot evaluate to `VALID` by vacuous truth. They enter
`MONITORING_UNAVAILABLE` / fail-closed handling once detected for an active
pending remainder.

### 5.2 Activation rule

F-013 monitoring activates only after actual exchange acceptance/placement:

```text
Order Placed.decision_cycle_id == frozen_condition.decision_cycle_id
AND
Order Placed.set_result_id == frozen_condition.set_result_id
AND
Order Placed.tranche_id is the tranche linked to that matched cycle
```

Set must not activate monitoring by symbol, order timestamp, nearest order,
latest Set result or current market configuration.

If activation identity cannot be resolved unambiguously, monitoring activation
fails closed and records an integrity/reconciliation condition. Set does not
guess an order and does not emit a market cancel signal for an unidentified
order.

### 5.3 Per-condition evaluation

Each hard condition evaluates to one of:

```text
TRUE
FALSE
UNAVAILABLE
INVALID_CONDITION
```

Evaluation uses only the frozen predicate definition and the current factual
measurements explicitly selected by that frozen definition. It may use current
measurements, completed bars, reference events or data-stream health only when
the frozen condition calls for them. It never updates the original threshold,
reference identity, configuration binding or condition list.

For Set-derived numeric dependencies:

- use canonical `TT_SET_NUMERIC_V1` working values where applicable;
- use exact comparisons with no epsilon;
- exclude incomplete/still-forming candles unless a different approved factual
  source is explicitly selected;
- treat missing, ambiguous, ineligible or incomplete required evidence as
  `UNAVAILABLE`.

### 5.4 Outcome precedence

For an active monitor, F-013 reduces evidence to exactly one monitor outcome in
this order:

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
another condition, because the order is already disqualified by established
market evidence. Authoritative terminal remainder state takes precedence over
market evaluation because no active pending remainder remains for Set to govern.

### 5.5 Cancel signal semantics

When the outcome is `INVALID`, Set emits one idempotent cancel signal for the
same invalidation event:

```yaml
order_cancel_signal:
  contract_version: 2
  signal_id: deterministic-id
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

`invalidated_at` is the authoritative effective time of the evidence that made
the hard condition TRUE, not the time the cancel request later reaches the
exchange.

Repeated evaluation of the same frozen condition, same evidence digest and same
active unfilled remainder produces the same logical cancel signal or an
idempotent replay of it, not a new logical cancellation event.

### 5.6 Unavailable fail-safe semantics

When outcome is `UNAVAILABLE`, Set records the unavailable state and requests
fail-closed handling for the active pending remainder. Because Lifecycle owns
order state, the required sequence is:

```text
Set marks MONITORING_UNAVAILABLE
→ reconcile order state first
→ if authoritative Lifecycle evidence proves no active unfilled remainder:
     STOPPED, no market cancel signal
→ if still pending:
     emit or preserve the cancel-required signal/intention for the unfilled
     remainder
```

Market recovery after this point must not silently erase an already required
unavailable cancellation for the same active remainder. A later authoritative
terminal event may stop the monitor; otherwise cancellation remains required
until Lifecycle terminal truth is reconciled.

### 5.7 Stop semantics

Monitoring stops only when Order Lifecycle authoritatively confirms that no
active unfilled entry remainder remains because the entry is fully filled,
cancelled, rejected, submission failed or otherwise terminal.

Set must not infer stop state from market data, local timeout or absence of an
open order in an unrelated snapshot.

For partial fill:

```text
filled quantity -> real exposure governed by TP / SL / Manual Close
unfilled remainder -> remains under F-013 until terminal or cancelled
```

F-013 never closes already filled exposure.

## 6. Inputs

| Input | Required semantics |
|---|---|
| `decision_cycle_id` | Set-created matched cycle identity. |
| `set_result_id` | Set-created matched result identity. |
| `tranche_id` | Linked tranche identity from Position/Order Lifecycle. |
| `symbol` | Same instrument as the matched Set cycle. |
| `Order Placed` | Actual exchange acceptance/placement event; activates monitor. |
| Frozen condition record | Nonempty deterministic hard-condition list persisted at Set match. |
| Current factual evidence | Only evidence selected by the frozen condition. |
| Evidence eligibility/coverage | Required for AVAILABLE condition evaluation. |
| Lifecycle terminal/remainder state | Authoritative source for STOPPED and cancel targeting. |

## 7. Outputs

State output:

```text
pending_validity = VALID | INVALID | UNAVAILABLE | STOPPED
```

Action output:

```text
NO_MESSAGE
NO_MARKET_SIGNAL
EMIT_ORDER_CANCEL_SIGNAL
FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING
```

There is no KEEP signal.

## 8. Units

F-013 has no native numeric unit. Each hard condition inherits units from its
referenced metric, formula, threshold, price level, timestamp or state source.

## 9. Parameters and Thresholds

F-013 has no universal threshold. Each deployable Set version must pin its
hard-condition thresholds/references, timeframes/horizons, freshness and
unavailable policy.

Threshold calibration and condition-set performance are research questions
unless separately approved. A certified F-013 framework does not claim any
condition set is profitable.

## 10. Sign and Direction Semantics

The monitor preserves the original Set-owned `LONG` or `SHORT` direction. It
does not reclassify direction and does not allow Order Lifecycle or Position
Rules to reinterpret direction. Direction may be a frozen condition input only
when explicitly persisted in the condition record.

## 11. Domain / Preconditions

F-013 applies only to a matched Set cycle with a persisted frozen condition
record and a later actual `Order Placed` event for an active pending LIMIT entry.

It does not apply to unmatched Set evaluations, submission attempts without
exchange acceptance, definitive no-create failures, market orders, already
terminal entry remainders or filled exposure after the entry remainder is gone.

## 12. Missing / Invalid Behavior

| Condition | Behavior |
|---|---|
| Empty hard-condition list | Invalid frozen condition; unavailable/fail-closed handling, not VALID. |
| Missing/malformed condition field | `INVALID_CONDITION`; unavailable/fail-closed handling. |
| Unsupported operator or metric reference | `INVALID_CONDITION`; unavailable/fail-closed handling. |
| Ambiguous activation identity | Fail closed with integrity/reconciliation condition; do not guess order. |
| Missing required market data | `UNAVAILABLE`; fail-closed handling. |
| Late data for a frozen selector | Use only if it belongs to the persisted selector and remains eligible; otherwise keep unavailable/reconcile. |
| Current Set no longer fully matches | Not an invalidator unless a frozen hard condition says so. |
| Newer opportunity exists | Not an invalidator for this monitor. |
| Coins CLOSE | Stops new formations only; does not stop this monitor. |
| Arbitrary short order age | Not an invalidator. |

## 13. Boundaries

Set owns market-validity state and cancel-signal production.

Order Lifecycle owns exchange order state, cancel execution, fill/remainder
reconciliation and terminal entry events.

Portfolio owns capital accounting and release after receiving lifecycle/accounting
events. Position Rules owns trade construction but not F-013 monitoring.

## 14. Precision / Comparison

Use exact canonical values from the referenced frozen metric or source. For
Set-derived arithmetic, use `TT_SET_NUMERIC_V1` and exact comparisons without
epsilon. Equality-boundary behavior follows the operator persisted in the frozen
condition record.

No display rounding may feed an F-013 gate.

## 15. Time Semantics

Monitoring starts only after actual `Order Placed`.

Evaluation is event/condition-driven. Triggers may include:

- new relevant completed bar;
- reference-level event;
- market-data event required by the frozen condition;
- data-stream health change;
- reconnect/recovery.

For completed-candle evidence, a candle ending after the persisted as-of cutoff
or still forming at evaluation time is ineligible unless a separate approved
condition explicitly selects another factual mode.

## 16. State / Replay / Restart

F-013 persists:

- frozen condition record and digest;
- activation identity;
- monitor state;
- last evaluated evidence identity/digest;
- emitted cancel signal identity;
- unavailable/fail-closed requirement;
- Lifecycle terminal/tombstone revisions used to stop the monitor.

Restart restores these facts. It must not rebuild a condition from current
configuration, latest Set result, current snapshot, nearest order or current
market data.

## 17. Configuration Pinning

The Set/Trigger/Core Set configuration selected for the formation epoch is
pinned for the matched cycle. Later configuration edits apply only to later
cycles and do not mutate existing monitors.

The condition record must include configuration identity, version and content
digest.

## 18. Dependencies

| Dependency | Classification | Use |
|---|---|---|
| F-001 through F-005 | CERTIFIED_FORMULA | Possible frozen Set metric/direction dependencies, when referenced by a concrete condition. |
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Set numeric precision, exact comparison and evidence eligibility. |
| SYSTEM_PROTOCOLS P16/S04/P17 | DOCUMENTATION_DEPENDENCY | Selector binding, historical evidence eligibility and immutable configuration binding. |
| Order Lifecycle pending-entry state | DOCUMENTATION_DEPENDENCY | Authoritative activation, cancel target and stop state. |
| Concrete hard-condition thresholds | CONFIG_PARAMETER / RESEARCH_PARAMETER | Versioned Set configuration; performance remains empirical. |

## 19. Ownership

Owner: Set.

F-013 approval is certification evidence only. It does not approve backend
implementation, deployment, TESTING/ACTIVE promotion, live or paper execution,
exchange interaction or any runtime order cancellation.

## 20. Pipeline Role

```text
Set MATCHED
→ frozen condition record retained inside Set
→ Market Handoff to Position Rules
→ downstream approval/construction/authorization
→ Order Placed returns to Set
→ F-013 monitor active for unfilled entry remainder
→ no message while VALID
→ cancel signal if INVALID or unavailable fail-safe requires cancellation
→ monitor stops only on authoritative Lifecycle terminal remainder state
```

## 21. Approved Uses

If approved, F-013 may be used as the certified generic state predicate for
Set-owned pending LIMIT entry market-validity monitoring.

## 22. Prohibited Interpretations

F-013 must not be interpreted as:

- approval of any arbitrary hard-condition set;
- permission to cancel due to ordinary signal flicker;
- permission to close filled exposure;
- an order-management component;
- a reprice/chase/replace algorithm;
- a profitability claim;
- a timer-based TTL;
- a substitute for Lifecycle reconciliation;
- a backend implementation approval.

## 23. Known Limitations

- Concrete condition sets need their own versioned configuration and may require
  separate review before final deployment.
- Cancellation may race fills and cannot guarantee the exchange prevents all
  subsequent execution before cancellation is accepted.
- Operational detection latency is not specified by F-013.
- Empirical benefit is unproven.

## 24. Research Parameters

- Concrete hard-condition thresholds.
- Freshness windows beyond already approved factual-source rules.
- Any condition-specific tolerance or reference-level interpretation not already
  certified.

## 25. Empirical Validation Requirements

Before treating a concrete F-013 condition set as trading-performance optimal,
research must evaluate adverse-fill reduction, missed profitable fills,
cancellation/re-entry cost, unavailable-data cancellation frequency, detection
latency and fast-market partial-fill exposure.

## 26. Acceptance Cases

| Case | Setup | Expected outcome |
|---|---|---|
| Hard TRUE and another condition UNAVAILABLE | Active remainder; condition A TRUE; condition B missing | `INVALID`; emit cancel signal for A. |
| All conditions FALSE | Active remainder; all evidence eligible | `VALID`; no message. |
| One condition UNAVAILABLE, none TRUE | Active remainder; required evidence missing | `UNAVAILABLE`; reconcile then cancel if still pending. |
| Empty condition list | Active remainder; no valid hard condition | `UNAVAILABLE`; fail closed, not VALID. |
| Malformed operator | Active remainder; unsupported operator | `UNAVAILABLE`; fail closed. |
| Equality boundary | Condition operator `GTE`, value equals threshold | TRUE. For `GT`, same value is FALSE. |
| Current Set no longer fully matches | No frozen hard predicate TRUE | Not by itself invalid; evaluate frozen predicates only. |
| Newer opportunity appears | Existing cycle A has active monitor; new cycle B forms | Cycle A unchanged; B has independent identity. |
| Coins CLOSE after match | Active monitor exists | New formation stops; monitor continues until Lifecycle terminal state. |
| Duplicate Order Placed replay | Same identity and lifecycle revision | Idempotent activation; no new monitor. |
| Terminal event before delayed Order Placed | Lifecycle terminal tombstone exists | `STOPPED`; delayed placement cannot reactivate. |
| Partial fill before invalidation | Filled quantity plus active remainder | Cancel signal targets unfilled remainder only; filled exposure remains governed by TP / SL / Manual Close. |
| Full fill before invalidation evaluation | No active unfilled remainder | `STOPPED`; no market cancel signal. |
| Outage then recovery, still pending | Monitor unavailable during outage; reconciliation proves still pending | Cancellation remains required unless terminal evidence appears. |
| Restart after emitted cancel signal | Same frozen condition and evidence digest restored | Same logical signal/idempotent replay; no new logical invalidation event. |
| Later configuration edit | Existing monitor active | Existing frozen condition remains unchanged. |

## 27. Final Council Review Request

Council should re-review whether this revised specification resolves:

- B1 outcome precedence;
- B2 frozen-condition validity;
- B3 cancellation/event progression;
- B4 dependency evidence;
- B5 acceptance examples;

and whether F-013 can be approved as a generic Set-owned system formula/state
predicate with limitations that concrete condition sets still require versioned
configuration and empirical validation.
