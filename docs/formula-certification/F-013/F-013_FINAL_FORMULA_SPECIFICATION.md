# FINAL_FORMULA_SPECIFICATION

# F-013 - Set Pending Invalidation and Stale-Signal Eligibility

**Artifact:** `F-013_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review - Cycle 2
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | F-013 |
| Formula name | Set pending invalidation and stale-signal eligibility |
| Owner | Set |
| Formula family | SYSTEM_FORMULA |
| Reviewed candidate | `F-013_REVISED_SPEC_CYCLE_1` |
| Active methodology baseline | v1.2.14 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = FIT_FOR_STATED_PENDING_ENTRY_CONTROL_ROLE
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = NOT_ESTABLISHED
IMPLEMENTATION_AND_LIVE_DEPLOYMENT = NOT_CERTIFIED
```

Approval covers the generic Set-owned pending-entry control framework. It does
not certify concrete condition sets, calibrated thresholds, live implementation
readiness, profitability, deployment, TESTING/ACTIVE promotion or exchange
interaction.

## 3. Intended Purpose

F-013 defines the deterministic Set-owned state predicate for an already placed
pending LIMIT entry:

```text
Does the original frozen Set market-validity condition remain valid, become
invalid, become unavailable, or stop because no active unfilled entry remainder
exists?
```

## 4. Actual Construct

F-013 is a state predicate over:

- a matched Set cycle with persisted frozen Market Invalidation Inputs;
- actual `Order Placed` activation identity returned by Order Lifecycle;
- current eligible factual evidence required by frozen hard conditions;
- authoritative Order Lifecycle state for the active unfilled entry remainder.

F-013 is not a new indicator and has no universal standalone numeric threshold.
The framework requires valid, nonempty versioned hard conditions for any Set
version that can create a pending LIMIT entry.

## 5. Exact Formula / Rule

### 5.1 Frozen condition record

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
malformed or unsupported condition sets cannot evaluate to `VALID`.

### 5.2 Activation

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

### 5.3 Per-condition evaluation

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

### 5.4 Outcome precedence

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

### 5.5 Cancel signal

When `INVALID`, Set emits one idempotent cancel signal:

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
the hard condition TRUE. Repeated evaluation of the same frozen condition,
evidence digest and active remainder produces the same logical signal or an
idempotent replay.

### 5.6 Unavailable fail-safe

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

### 5.7 Stop rule

Monitoring stops only when Order Lifecycle authoritatively confirms no active
unfilled entry remainder remains because the entry is fully filled, cancelled,
rejected, submission failed or otherwise terminal.

F-013 never closes already filled exposure.

## 6. Inputs

| Input | Semantics |
|---|---|
| `decision_cycle_id` | Set-created matched cycle identity. |
| `set_result_id` | Set-created matched result identity. |
| `tranche_id` | Linked tranche identity from Position/Order Lifecycle. |
| `symbol` | Same instrument as the matched Set cycle. |
| `Order Placed` | Actual exchange acceptance/placement event. |
| Frozen condition record | Nonempty deterministic hard-condition list persisted at Set match. |
| Current factual evidence | Only evidence selected by the frozen condition. |
| Evidence eligibility/coverage | Required for AVAILABLE condition evaluation. |
| Lifecycle terminal/remainder state | Authoritative source for STOPPED and cancel targeting. |

## 7. Outputs

```text
pending_validity = VALID | INVALID | UNAVAILABLE | STOPPED
action =
  NO_MESSAGE
  | NO_MARKET_SIGNAL
  | EMIT_ORDER_CANCEL_SIGNAL
  | FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING
```

There is no KEEP signal.

## 8. Units

F-013 has no native numeric unit. Hard conditions inherit units from their
referenced metric, formula, threshold, price level, timestamp or state source.

## 9. Parameters

F-013 has no universal threshold. Each deployable Set version pins condition
thresholds/references, timeframes/horizons, freshness and unavailable policy.

## 10. Domain / Preconditions

F-013 applies only to a matched Set cycle with a persisted frozen condition
record and later actual `Order Placed` event for an active pending LIMIT entry.

It does not apply to unmatched evaluations, submission attempts without exchange
acceptance, definitive no-create failures, market orders, terminal entry
remainders or filled exposure after the entry remainder is gone.

## 11. Missing / Invalid Behavior

| Condition | Behavior |
|---|---|
| Empty hard-condition list | Invalid frozen condition; unavailable/fail-closed handling, not `VALID`. |
| Missing/malformed condition field | `INVALID_CONDITION`; unavailable/fail-closed handling. |
| Unsupported operator/reference | `INVALID_CONDITION`; unavailable/fail-closed handling. |
| Ambiguous activation identity | Fail closed with integrity/reconciliation condition; do not guess order. |
| Missing required market data | `UNAVAILABLE`; fail-closed handling. |
| Current Set no longer fully matches | Not an invalidator unless a frozen hard condition says so. |
| Newer opportunity exists | Not an invalidator for this monitor. |
| Coins CLOSE | Stops new formations only; does not stop this monitor. |
| Arbitrary order age | Not an invalidator. |

## 12. Boundaries

Set owns market-validity state and cancel-signal production. Order Lifecycle
owns exchange order state, cancel execution, fill/remainder reconciliation and
terminal entry events. Portfolio owns capital accounting and release. Position
Rules owns trade construction but not F-013 monitoring.

## 13. Precision / Rounding

Use exact canonical values from the referenced frozen metric or source. For
Set-derived arithmetic, use `TT_SET_NUMERIC_V1` and exact comparisons without
epsilon. Equality-boundary behavior follows the persisted operator.

## 14. Time Semantics

Monitoring starts only after actual `Order Placed`. Evaluation is
event/condition-driven and may be triggered by new relevant completed bars,
reference-level events, required market-data events, data-stream health changes
or reconnect/recovery.

## 15. State / Replay / Restart

F-013 persists condition record and digest, activation identity, monitor state,
last evidence identity/digest, emitted cancel signal identity,
unavailable/fail-closed requirement and Lifecycle terminal/tombstone revisions.

Restart restores these facts. It must not rebuild a condition from current
configuration, latest Set result, current snapshot, nearest order or current
market data.

## 16. Configuration Pinning

The Set/Trigger/Core Set configuration selected for the formation epoch is
pinned for the matched cycle. Later edits apply only to later cycles. The
condition record includes configuration identity, version and content digest.

## 17. Dependencies

| Dependency | Classification | Use |
|---|---|---|
| F-001 through F-005 | CERTIFIED_FORMULA | Possible frozen Set metric/direction dependencies when referenced by a concrete condition. |
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Set numeric precision, exact comparison and evidence eligibility. |
| SYSTEM_PROTOCOLS P16/S04/P17 | DOCUMENTATION_DEPENDENCY | Selector binding, historical evidence eligibility and immutable configuration binding. |
| Order Lifecycle pending-entry state | DOCUMENTATION_DEPENDENCY | Authoritative activation, cancel target and stop state. |
| Concrete condition thresholds | CONFIG_PARAMETER / RESEARCH_PARAMETER | Versioned Set configuration; performance remains empirical. |

## 18. Ownership

Owner: Set.

## 19. Pipeline Role

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

## 20. Approved Uses

F-013 may be used as the certified generic state predicate for Set-owned pending
LIMIT entry market-validity monitoring.

## 21. Prohibited Interpretations

F-013 is not:

- approval of any arbitrary hard-condition set;
- permission to cancel due to ordinary signal flicker;
- permission to close filled exposure;
- an order-management component;
- a reprice/chase/replace algorithm;
- a profitability claim;
- a timer-based TTL;
- a substitute for Lifecycle reconciliation;
- backend implementation approval.

## 22. Known Limitations

- Concrete condition sets need versioned configuration and may require separate
  review before deployment.
- Cancellation may race fills.
- Operational detection latency is not specified.
- Empirical benefit is unproven.

## 23. Research Parameters

- Concrete hard-condition thresholds.
- Freshness windows beyond already approved factual-source rules.
- Condition-specific tolerance or reference-level interpretation not already
  certified.

## 24. Empirical Validation Requirements

Research must evaluate adverse-fill reduction, missed profitable fills,
cancellation/re-entry cost, unavailable-data cancellation frequency, detection
latency and fast-market partial-fill exposure before any concrete condition set
is treated as performance-optimal.

## 25. Eight Final Expert Verdicts

| Expert perspective | Final verdict |
|---|---|
| Senior Intraday Crypto Trader | APPROVED |
| Market Microstructure & Order Flow Researcher | APPROVED |
| Market Regime & Context Analyst | APPROVED |
| Quant Strategy Researcher | APPROVED |
| Risk & Trade Management Architect | APPROVED |
| Execution & Exchange Mechanics Specialist | APPROVED |
| Adversarial Strategy Reviewer | APPROVED |
| Performance & Strategy Diagnostics Analyst | APPROVED |

## 26. Final Council Record

```text
FULL_COUNCIL_APPROVED = YES
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
SPECIFICATION_STATUS = APPROVED_FOR_FRAMEWORK_CERTIFICATION
TRADING_FITNESS_STATUS = FIT_FOR_STATED_PENDING_ENTRY_CONTROL_ROLE
BLOCKING_FINDINGS = NONE
```
