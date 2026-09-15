# F-013 Source Pack

# F-013 - Set Pending Invalidation and Stale-Signal Eligibility

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-013 |
| Formula name | Set pending invalidation and stale-signal eligibility |
| Owner | Set |
| Formula family | SYSTEM_FORMULA |
| Certification phase | Source Pack |
| Active methodology baseline | v1.2.14 |
| Source Pack status | Immutable pre-review provenance |

F-013 covers Set-owned market-validity monitoring for an already placed pending
LIMIT entry created from a matched Set result.

## 2. Source Index

| Source | Evidence |
|---|---|
| `docs/FORMULA_METRICS_CATALOG.md` | Catalog row marks F-013 as REVIEW_NEEDED; exact boundary between final Set calculation and state-only lifecycle behavior needs review. |
| `docs/trading-methodology/methodology/SET.md` lines 60-74 | Set has `INITIAL_ANALYSIS` and `PENDING_ORDER_MONITORING`; pending monitoring asks whether the still-pending LIMIT order remains valid under frozen invalidation conditions. |
| `docs/trading-methodology/methodology/SET.md` lines 156-166 | `Coins CLOSE` stops new-opportunity analysis but does not automatically terminate monitoring of an already placed pending order. |
| `docs/trading-methodology/methodology/SET.md` lines 181-220 | OPEN/CLOSE formation epochs reset unfinished pre-MATCH state only; `Order Placed` activates monitoring of frozen Market Invalidation Inputs tied to the originating decision cycle. |
| `docs/trading-methodology/methodology/SET.md` lines 319-328 | Pending monitoring responsibilities: activate frozen predicates, obtain required current values, evaluate only frozen predicates, emit cancel signal on hard invalidation, treat missing data as unavailable. |
| `docs/trading-methodology/methodology/SET.md` lines 431-456 | Set emits no message while valid; on invalidation it emits `Order Cancel Signal`; Order Lifecycle owns actual cancellation. |
| `docs/trading-methodology/methodology/SET.md` lines 514-525 | Market Invalidation Inputs, pending-order monitoring state, cancel signal and live validity status remain Set-owned and are not part of Position Rules Market Handoff. |
| `docs/trading-methodology/methodology/SET.md` lines 4075-4115 | Pending Order Market Validity runtime sequence and Set/Lifecycle responsibility split. |
| `docs/trading-methodology/methodology/SET.md` lines 4117-4151 | Frozen market-invalidation shape and requirement to store deterministic conditions frozen at original Set match. |
| `docs/trading-methodology/methodology/SET.md` lines 4154-4188 | Valid condition categories: thesis invalidation, direction/context contradiction, entry-context invalidation. |
| `docs/trading-methodology/methodology/SET.md` lines 4192-4204 | Non-invalidators: cooldown expiry, newer opportunity, slight price move, non-critical metric change, loss of full Set match, arbitrary short timer. |
| `docs/trading-methodology/methodology/SET.md` lines 4208-4235 | Fresh formation and pending-order monitoring are independent Set scopes. |
| `docs/trading-methodology/methodology/SET.md` lines 4238-4252 | Validation is event/condition-driven, not semantically defined by arbitrary fixed polling. |
| `docs/trading-methodology/methodology/SET.md` lines 4256-4282 | Outage behavior: unreliable market data makes validity `UNAVAILABLE`; if still pending after reconciliation, cancel. |
| `docs/trading-methodology/methodology/SET.md` lines 4286-4334 | Zero-fill and partial-fill invalidation flows; cancel unfilled remainder only. |
| `docs/trading-methodology/methodology/SET.md` lines 4351-4370 | Auto-reprice is disabled; invalid pending entry is cancelled and any future opportunity requires a new Set cycle. |
| `docs/trading-methodology/methodology/SET.md` lines 4374-4399 | Runtime invariants for pending monitoring, frozen conditions, unavailable data, no look-ahead and auditability. |
| `docs/trading-methodology/methodology/SET.md` lines 4447-4451 | Decision-cycle Frozen Condition binding; `Order Placed.decision_cycle_id` selects exact persisted Frozen Condition. |
| `docs/trading-methodology/methodology/SET.md` lines 4459-4463 | Analytical selector and historical evidence eligibility for new analysis and pending-cycle monitoring. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 127-145 | Order Lifecycle boundary: Set owns pending-order market validity; Lifecycle executes cancellation. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 600-624 | Pending LIMIT entry has no automatic TTL; it may end through fill, Set cancel signal, manual cancel, exchange rejection/expiry or reconciliation. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 707-728 | Set market invalidation cancel input and minimum correlation; Lifecycle verifies identity/current state and cancels unfilled remainder only. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1385-1439 | Set locates frozen conditions by decision cycle; Lifecycle terminal events stop/update pending monitor and do not change market logic. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1570-1597 | Invariants: no reprice/chase/fallback, Set invalidation never closes filled exposure, no arbitrary TTL, Set owns market validity. |
| `docs/formula-certification/F-005/F-005_FINAL_FORMULA_SPECIFICATION.md` | Certified Set direction classifier and Market Handoff/no-handoff boundary. |
| `docs/formula-certification/F-001/F-001_FINAL_FORMULA_SPECIFICATION.md` | Certified price-move trigger evidence. |
| `docs/formula-certification/F-002/F-002_FINAL_FORMULA_SPECIFICATION.md` | Certified volume confirmation evidence. |
| `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | Certified ATR/true-range evidence. |
| `docs/formula-certification/F-004/F-004_FINAL_FORMULA_SPECIFICATION.md` | Certified normalization, percentile, score and Set diagnostics evidence. |

## 3. Purpose and Trading Context

F-013 answers:

```text
For an already placed pending LIMIT entry, does the original Set-owned frozen
market-validity condition remain valid, become invalid, or become unavailable?
```

Trading role:

- prevent a stale pending LIMIT entry from remaining live after the original
  hard market thesis is invalidated;
- avoid canceling valid pending orders merely because a minor signal flickers or
  a new opportunity appears;
- keep Set market analysis separate from Order Lifecycle execution mechanics;
- preserve the original matched decision-cycle context through restart/replay;
- keep filled exposure governed by TP / SL / Manual Close rather than by
  pending-entry invalidation.

F-013 does not determine LONG/SHORT direction, compute entry/stop/take-profit,
size a position, approve capital, place or cancel exchange orders directly,
manage open exposure, or prove profitability.

## 4. Exact Formula If Available

The active methodology defines the governing state machine and condition shape,
but does not provide one universal numeric predicate list for all Set versions.

Candidate canonical rule extracted from sources:

```text
When Order Placed for decision_cycle_id/set_result_id/tranche_id is accepted:
  locate the exact frozen Market Invalidation Inputs persisted for that
  matched Set cycle.

While the entry has an active unfilled remainder:
  evaluate only those frozen hard invalidation predicates using their
  specified metric/reference, operator, threshold/reference, timeframe/horizon,
  freshness and unavailable policy.

If a hard predicate is TRUE:
  pending_validity = INVALID
  emit Order Cancel Signal.

If all required predicates are deterministically FALSE and all required evidence
is available/eligible:
  pending_validity = VALID
  emit no message.

If required market data/evidence is unreliable, incomplete, unavailable or
ineligible under the frozen condition's unavailable policy:
  pending_validity = UNAVAILABLE
  after reconciling order state first, cancel the still-pending unfilled entry
  remainder if it remains pending.

When Order Lifecycle reports terminal entry state for the unfilled remainder:
  stop/update the monitor for that decision cycle.
```

Only explicit hard-validity conditions should cancel. There is no KEEP signal.

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `decision_cycle_id` | Set-created matched cycle; returned by Order Placed | Selects exact frozen condition. |
| `set_result_id` | Set-created matched result; Order Placed / lifecycle events | Binds monitor to original Set result. |
| `tranche_id` | Position/Order Lifecycle identity | Correlates pending entry remainder and cancel signal. |
| `symbol` | Matched Set result / Order Placed | Same instrument as the original matched cycle. |
| `order_placed_at` | Order Lifecycle | Activates monitoring only after actual exchange acceptance. |
| Frozen Market Invalidation Inputs | Set internal persisted state | Deterministic predicates frozen at Set match. |
| `hard_conditions[]` | Frozen condition record | Condition ID, metric/reference, operator, threshold/reference, timeframe/horizon, freshness and unavailable policy. |
| Current required market/derived metric values | Set/API factual evidence | Must satisfy condition-specific selector, timeframe and freshness requirements. |
| Evidence eligibility/coverage state | Set/API/SYSTEM_PROTOCOLS S04 | Determines whether inputs are eligible or unavailable. |
| Entry lifecycle terminal event | Order Lifecycle | Stops/updates monitor without changing market logic. |
| Entry filled/remainder state | Order Lifecycle | Determines whether cancel applies to unfilled remainder only. |

## 6. Outputs

Primary state output:

```text
pending_validity = VALID | INVALID | UNAVAILABLE | STOPPED
```

External message when invalid/unavailable-cancel requires action:

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

No output message is emitted while the pending entry remains valid.

## 7. Units

F-013 itself is a state predicate, not a new numeric indicator.

Any numeric units used inside `hard_conditions[]` inherit the units of the
frozen referenced formula, metric or level, including certified Set formulas
where applicable.

## 8. Parameters

F-013 has no standalone universal numeric threshold.

Versioned Set configurations must pin their own hard invalidation conditions,
including any threshold/reference, timeframe/horizon, freshness and unavailable
policy. Such values are configuration or research parameters unless separately
certified as formulas.

## 9. Thresholds

The source explicitly prohibits automatic cancellation from:

- cooldown expiry;
- newer Set opportunity;
- slight price movement;
- one non-critical metric change;
- current Set no longer fully matching;
- arbitrary short order age.

Only explicit hard validity conditions should cancel.

## 10. Sign / Direction Semantics

F-013 preserves the original Set-owned direction from the matched cycle.

Direction may be used by a frozen condition when the condition references a
directional thesis, context contradiction or entry-context invalidation. F-013
does not reclassify LONG/SHORT/NONE and does not authorize a direction change.

## 11. Domain / Preconditions

F-013 applies only when:

- a Set result was matched and created `decision_cycle_id` and `set_result_id`;
- the frozen Market Invalidation Inputs were persisted at match time;
- Order Lifecycle later reports actual placed/accepted pending LIMIT entry;
- the pending entry has an active unfilled remainder;
- the monitor can resolve the activation identity unambiguously.

If the identity cannot be resolved unambiguously, monitoring activation must fail
closed and surface an integrity/reconciliation error rather than guessing.

## 12. Boundaries

Set owns:

- market-validity analysis;
- frozen invalidation predicates;
- pending-order monitoring state;
- `Order Cancel Signal` production.

Order Lifecycle owns:

- submission state;
- exchange acceptance;
- cancel request execution;
- fill/remainder reconciliation;
- terminal entry lifecycle events.

Position Rules and Portfolio Rules do not own F-013 market-validity semantics.

## 13. Precision

F-013 inherits precision from each frozen referenced metric or formula. For
certified Set-derived arithmetic, `TT_SET_NUMERIC_V1` applies.

State comparison must be exact over canonical frozen condition content and
eligible evidence. No look-ahead is allowed.

## 14. Time Semantics

Monitoring starts only after `Order Placed` for the matching decision cycle.

Validation is event/condition-driven. Preferred triggers are:

- new relevant completed bar;
- reference-level event;
- market-data event required by the contract;
- data-stream health change;
- system reconnect/recovery.

Operational polling may exist but is not the semantic rule.

## 15. State / Replay / Restart

Set persists:

- original formation epoch and configuration binding;
- decision cycle and Set result identity;
- frozen condition record;
- monitor activation/stop state;
- lifecycle revision/tombstone information for terminal entry events;
- evidence selector/cutoff and eligibility status.

On replay/restart, Set reuses the persisted frozen condition and selection
identity. It must not replace the condition with the latest Set result, nearest
order, current configuration or current market snapshot.

## 16. Version / Configuration Pinning

The Set configuration selected when the current OPEN formation epoch is created
is pinned by P17. The matched cycle retains its exact binding.

The frozen invalidation condition must include Set version/family and
deterministic hard condition content. Later Set configuration edits do not alter
an existing pending monitor.

## 17. Ownership

Owner: Set.

F-013 remains certification evidence only. It does not authorize implementation,
deployment, TESTING/ACTIVE promotion, exchange interaction or live/paper order
activity.

## 18. Downstream Consumers

| Consumer | Use |
|---|---|
| Order Lifecycle | Receives `Order Cancel Signal` and cancels unfilled entry remainder if current state permits. |
| Portfolio Rules | Receives downstream Order Events and performs capital/accounting reconciliation. |
| Certification/system integration | Uses F-013 to validate that Set lifecycle and pending-order monitoring boundaries are coherent. |

## 19. Dependencies

| Dependency | Classification | Notes |
|---|---|---|
| F-001 | CERTIFIED_FORMULA | Possible frozen price-move/trigger evidence when selected by a Set version. |
| F-002 | CERTIFIED_FORMULA | Possible frozen volume-confirmation evidence when selected by a Set version. |
| F-003 | CERTIFIED_FORMULA | Possible volatility/reference context. |
| F-004 | CERTIFIED_FORMULA | Possible score/diagnostic evidence and Set analytics. |
| F-005 | CERTIFIED_FORMULA | Certified Set direction and handoff/no-handoff boundary. |
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Numeric representation for Set-derived arithmetic. |
| SYSTEM_PROTOCOLS P16/S04/P17 | DOCUMENTATION_DEPENDENCY | Evidence eligibility, historical assembly and configuration binding. |
| Order Lifecycle pending-entry state | DOCUMENTATION_DEPENDENCY | Determines activation/stop and whether an unfilled remainder exists. |
| Versioned hard invalidation condition content | CONFIG_PARAMETER / RESEARCH_PARAMETER | Must be pinned per Set version; source does not define one universal predicate list. |

## 20. Existing Worked Examples

Source examples:

```text
original LONG setup required support X
support X is decisively broken
→ INVALID
```

```text
planned entry was a pullback to a structural zone
market moved through / away in a way that destroys that setup
```

Flow examples:

```text
INVALID pending context
→ cancel remainder
→ keep filled exposure
```

```text
terminal event first
then delayed ORDER_PLACED
→ monitor remains STOPPED
```

## 21. Explicit Source Gaps

1. The active methodology defines categories and required frozen-condition
   structure, but does not enumerate a universal predicate list for every Set
   version.
2. The exact mapping from each certified Set trigger/score/reference into
   hard invalidation predicates is not fully enumerated in a formula-specific
   artifact.
3. The unavailable policy is specified generally as fail-safe cancellation for
   still-pending unfilled entries after reconciliation, but individual frozen
   hard conditions may need explicit unavailable-policy fields.
4. No empirical evidence proves that any particular hard-condition set improves
   profitability.

## 22. Reviewer Handoff Summary

Council should certify whether F-013 can be approved as a Set-owned system
formula/state predicate that:

- activates only from actual `Order Placed`;
- evaluates only deterministic frozen hard invalidation predicates tied to the
  original `decision_cycle_id/set_result_id`;
- emits no KEEP signal while valid;
- emits `Order Cancel Signal` only for hard invalidation or required
  unavailable fail-safe behavior;
- never closes filled exposure;
- never reprices/chases/replaces an order;
- does not require the entire Set to remain continuously matched;
- distinguishes independent fresh formations from existing pending monitors;
- preserves replay/restart determinism and configuration pinning.

Council should also decide whether the source gaps above are acceptable as
versioned configuration boundaries, require a revised F-013 candidate, or require
a product decision.
